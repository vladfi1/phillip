import os
import tensorflow as tf
import numpy as np
from enum import Enum
from . import ssbm, tf_lib as tfl, util, embed, ctype_util as ct
from .default import Default, Option
from .rl_common import *
from .ac import ActorCritic
from .critic import Critic
from .model import Model
from .core import Core
from .mutators import relative

class Mode(Enum):
  LEARNER = 0
  ACTOR = 1

class RL(Default):
  _options = [
    Option('tfdbg', action='store_true', help='debug tensorflow session'),
    Option('path', type=str, help="path to saved policy"),
    Option('gpu', action="store_true", default=False, help="run on gpu"),
    Option('action_type', type=str, default="diagonal", choices=ssbm.actionTypes.keys()),
    Option('name', type=str),
    Option('predict', type=int, default=0),
    Option('train_model', type=int, default=0),
    Option('train_policy', type=int, default=1),
    # in theory train_critic should always equal train_policy; keeping them
    # separate might help for e.g. debugging
    Option('train_critic', type=int, default=1), 
    Option('profile', type=int, default=0, help='profile tensorflow graph execution'),
    Option('save_cpu', type=int, default=0),
    Option('learning_rate', type=float, default=1e-4),
    Option('clip_max_grad', type=float, default=1.),
    # if pop_id >= 0, then we're doing population-based training, and pop_id 
    # tracks the worker's id. Else we're not doing PBT and the id is -1. 
    Option('pop_id', type=int, default=-1), 
    Option('reward_decay', type=float, default=1e-3),
    # evolve_leraning_rate is false by default; if true, then the learning rate
    # is included in PBT among the things that get mutated. 
    Option('evolve_learning_rate', action="store_true"),
    Option('explore_scale', type=float, default=0., help='use prediction error as additional reward'),
    Option('dynamic', type=int, default=1, help='use dynamic loop unrolling'),
  ]
  
  _members = [
    ('config', RLConfig),
    ('embedGame', embed.GameEmbedding),
    ('critic', Critic),
    ('model', Model),
    ('core', Core),
    #('opt', Optimizer),
  ]
  
  def __init__(self, mode=Mode.LEARNER, debug=False, **kwargs):
    Default.__init__(self, init_members=False, **kwargs)
    self.config = RLConfig(**kwargs)
    
    if self.name is None: self.name = "ActorCritic"
    if self.path is None: self.path = "saves/%s/" % self.name
    # the below is a hack that makes it easier to run phillip from the command
    # line, if we're doing PBT but don't want to specify the population ID. 
    if self.evolve_learning_rate and self.pop_id < 0: self.pop_id = 0
    if self.pop_id >= 0:
      self.root = self.path
      self.path = os.path.join(self.path, str(self.pop_id))
      print(self.path)
    # where trained agents get saved onto disk. 
    self.snapshot_path = os.path.join(self.path, 'snapshot')
    self.actionType = ssbm.actionTypes[self.action_type]
    
    # takes in action, and returns a one-hot vector corresponding to that action. 
    embedAction = embed.OneHotEmbedding("action", self.actionType.size)
    
    self.graph = tf.Graph()
    device = '/gpu:0' if self.gpu else '/cpu:0'
    print("Using device " + device)
    with self.graph.as_default(), tf.device(device): 
      # total number of gradient descent steps the learner has taken thus far
      self.global_step = tf.Variable(0, name='global_step', trainable=False)
      self.evo_variables = []
      
      self.embedGame = embed.GameEmbedding(**kwargs)
      state_size = self.embedGame.size
      combined_size = state_size + embedAction.size
      history_size = (1+self.config.memory) * combined_size
      print("History size:", history_size)

      self.components = {}
      self.core = Core(history_size, **kwargs)
      self.components['core'] = self.core
      
      # initialize predictive model, if either: 
      #  * you want to use the predictive model to "undo delay"
      #  * you want a predictive model to help you explore
      # note: self.predict is perhaps a misnomer. 
      if self.predict or (mode == Mode.LEARNER and (self.train_model or self.explore_scale)):
        print("Creating model.")
        self.model = Model(self.embedGame, embedAction.size, self.core, self.config, **kwargs)
        self.components['model'] = self.model
        self.predict = True

      if mode == Mode.ACTOR or self.train_policy:
        effective_delay = self.config.delay
        if self.predict:
          effective_delay -= self.model.predict_steps
        input_size = self.core.output_size + effective_delay * embedAction.size
        
        self.policy = ActorCritic(input_size, embedAction.size, self.config, **kwargs)
        self.components['policy'] = self.policy
        self.evo_variables.extend(self.policy.evo_variables)
      
      if mode == Mode.LEARNER:
        # to train the the policy, you have to train the critic. (self.train_policy and 
        # self.train_critic might both be false, if we're only training the predictive
        # model)
        if self.train_policy or self.train_critic:
          print("Creating critic.")
          self.critic = Critic(self.core.output_size, **kwargs)
          self.components['critic'] = self.critic

        # experience = trajectory. usually a list of SimpleStateAction's. 
        self.experience = ct.inputCType(ssbm.SimpleStateAction, [None, self.config.experience_length], "experience")
        # instantaneous rewards for all but the last state
        self.experience['reward'] = tf.placeholder(tf.float32, [None, self.config.experience_length-1], name='experience/reward')
        # manipulating time along the first axis is much more efficient
        experience = util.deepMap(tf.transpose, self.experience)       
        # initial state for recurrent networks
        self.experience['initial'] = tuple(tf.placeholder(tf.float32, [None, size], name='experience/initial/%d' % i) for i, size in enumerate(self.core.hidden_size))
        experience['initial'] = self.experience['initial']

        states = self.embedGame(experience['state'])
        prev_actions = embedAction(experience['prev_action'])
        combined = tf.concat(axis=2, values=[states, prev_actions])
        actions = embedAction(experience['action'])

        memory = self.config.memory
        delay = self.config.delay
        length = self.config.experience_length - memory
        history = [combined[i:i+length] for i in range(memory+1)]
        inputs = tf.concat(axis=-1, values=history)
        if self.core.recurrent:
          def f(prev, current_input):
            _, prev_state = prev
            return self.core(current_input, prev_state)
          batch_size = tf.shape(self.experience['reward'])[0]
          dummy_output = tf.zeros(tf.stack([batch_size, tf.constant(self.core.output_size)]))
          scan_fn = tf.scan if self.dynamic else tfl.scan
          core_outputs, hidden_states = scan_fn(f, inputs, (dummy_output, experience['initial']))
        else:
          core_outputs, hidden_states = self.core(inputs, experience['initial'])

        actions = actions[memory:]
        rewards = experience['reward'][memory:]
        
        print("Creating train ops")

        train_ops = []
        losses = []
        loss_vars = []

        if self.train_model or self.predict:
          model_loss, predicted_core_outputs = self.model.train(history, core_outputs, hidden_states, actions, experience['state'])
        if self.train_model:
          #train_ops.append(train_model)
          losses.append(model_loss)
          loss_vars.extend(self.model.getVariables())
        
        if self.train_policy:
          if self.predict:
            predict_steps = self.model.predict_steps
            actor_inputs = predicted_core_outputs
          else:
            predict_steps = 0
            actor_inputs = core_outputs
          
          delay_length = length - delay
          actor_inputs = actor_inputs[:delay_length]

          # delayed_actions is a D+1-P length list of shape [T-M-D, B] tensors
          # The valid state indices are [M+P, T+P-D)
          # Element i corresponds to the i'th queued up action: 0 is the action about to be taken, D-P was the action chosen on this frame.
          delayed_actions = []
          for i in range(predict_steps, delay+1):
            delayed_actions.append(actions[i:i+delay_length])
          train_probs, train_log_probs, entropy = self.policy.train_probs(actor_inputs, delayed_actions)
          
          behavior_probs = experience['prob'][memory+delay:] # these are the actions we can compute probabilities for
          prob_ratios = tf.minimum(train_probs / behavior_probs, 1.)
          self.kls = -tf.reduce_mean(tf.log(prob_ratios), 0)
          self.kls = tf.check_numerics(self.kls, 'kl')
          kl = tf.reduce_mean(self.kls)
          tf.summary.scalar('kl', kl)
        else:
          prob_ratios = tf.ones_like() # todo

        if self.explore_scale:
          self.explore_scale = tf.Variable(self.explore_scale, trainable=False, name='explore_scale')
          self.evo_variables.append(('explore_scale', self.explore_scale, relative(1.5)))
          
          distances, _ = self.model.distances(history, core_outputs, hidden_states, actions, experience['state'], predict_steps=1)
          distances = tf.add_n(list(util.deepValues(distances))) # sum over different state components
          explore_rewards = self.explore_scale * distances[0]
          explore_rewards = tf.stop_gradient(explore_rewards)
          rewards += explore_rewards

        # build the critic (which you'll also need to train the policy)
        if self.train_policy or self.train_critic:
          critic_loss, targets, advantages = self.critic(core_outputs[delay:], rewards[delay:], prob_ratios[:-1])
        
        if self.train_critic:
          losses.append(critic_loss)
          loss_vars.extend(self.critic.variables)
        
        if self.train_policy:
          policy_loss = self.policy.train(train_log_probs[:-1], advantages, entropy[:-1])
          losses.append(policy_loss)
          loss_vars.extend(self.policy.getVariables())

        if self.evolve_learning_rate:
          self.learning_rate = tf.Variable(self.learning_rate, trainable=False, name='learning_rate')
          self.evo_variables.append(('learning_rate', self.learning_rate, relative(1.5)))

        total_loss = tf.add_n(losses)
        with tf.variable_scope('train'):
          optimizer = tf.train.AdamOptimizer(self.learning_rate)
          gvs = optimizer.compute_gradients(total_loss)
          # gvs = [(tf.check_numerics(g, v.name), v) for g, v in gvs]
          gs, vs = zip(*gvs)
          
          norms = tf.stack([tf.norm(g) for g in gs])
          max_norm = tf.reduce_max(norms)
          tf.summary.scalar('max_grad_norm', max_norm)
          capped_gs = [tf.clip_by_norm(g, self.clip_max_grad) for g in gs]
          train_op = optimizer.apply_gradients(zip(capped_gs, vs))
          train_ops.append(train_op)
        
        print("Created train op(s)")
        
        avg_reward = tf.reduce_mean(experience['reward'])
        tf.summary.scalar('reward', avg_reward)
        
        misc_ops = []
        
        if not self.dynamic:
          misc_ops.append(tf.add_check_numerics_ops())
        
        if self.pop_id >= 0:
          self.reward = tf.Variable(0., trainable=False, name='avg_reward')
          tf.summary.scalar('avg_reward', self.reward)
          new_reward = (1. - self.reward_decay) * self.reward + self.reward_decay * avg_reward
          misc_ops.append(tf.assign(self.reward, new_reward))
        
        self.mutators = []
        for name, evo_variable, mutator in self.evo_variables:
          tf.summary.scalar(name, evo_variable, family='evolution')
          self.mutators.append(tf.assign(evo_variable, mutator(evo_variable)))
        
        self.summarize = tf.summary.merge_all()
        misc_ops.append(tf.assign_add(self.global_step, 1))
        self.misc = tf.group(*misc_ops)
        self.train_ops = tf.group(*train_ops)

        print("Creating summary writer at logs/%s." % self.name)
        #self.writer = tf.summary.FileWriter('logs/' + self.name)#, self.graph)
        self.writer = tf.summary.FileWriter(self.path)
      else:
        # with tf.name_scope('policy'):
        self.input = ct.inputCType(ssbm.SimpleStateAction, [self.config.memory+1], "input")
        self.input['delayed_action'] = tf.placeholder(tf.int64, [self.config.delay], "delayed_action")
        self.input['hidden'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [size], name="input/hidden"), self.core.hidden_size)

        states = self.embedGame(self.input['state'])
        prev_actions = embedAction(self.input['prev_action'])
        combined = tf.concat(axis=-1, values=[states, prev_actions])
        history = tf.unstack(combined)
        inputs = tf.concat(axis=-1, values=history)
        core_output, hidden_state = self.core(inputs, self.input['hidden'])
        actions = embedAction(self.input['delayed_action'])
        
        if self.predict:
          predict_actions = actions[:self.model.predict_steps]
          delayed_actions = actions[self.model.predict_steps:]
          core_output = self.model.predict(history, core_output, hidden_state, predict_actions, self.input['state'])
        else:
          delayed_actions = actions
        
        self.run_policy = self.policy.getPolicy(core_output, delayed_actions), hidden_state
      
      self.debug = debug
      
      self.variables = tf.global_variables()
      self.initializer = tf.global_variables_initializer()
      
      self.saver = tf.train.Saver(self.variables)
      
      self.placeholders = {v.name : tf.placeholder(v.dtype, v.get_shape()) for v in self.variables}
      self.unblobber = tf.group(*[tf.assign(v, self.placeholders[v.name]) for v in self.variables])
      
      self.graph.finalize()
      
      tf_config = dict(
        allow_soft_placement=True,
        #log_device_placement=True,
      )
      
      if self.save_cpu:
        tf_config.update(
          inter_op_parallelism_threads=1,
          intra_op_parallelism_threads=1,
        )
      
      self.sess = tf.Session(
        graph=self.graph,
        config=tf.ConfigProto(**tf_config),
      )
      
      if self.tfdbg:
        from tensorflow.python import debug as tf_debug
        self.sess = tf_debug.LocalCLIDebugWrapperSession(self.sess)

  def get_global_step(self):
    return self.sess.run(self.global_step)
  
  def get_reward(self):
    return self.sess.run(self.reward)

  def mutation(self, rate=1.):
    mutations = []
    for op in self.mutators:
      if np.random.random() < rate / len(self.mutators):
        mutations.append(op)
    self.sess.run(mutations)

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    policy, hidden = self.sess.run(self.run_policy, feed_dict)
    return self.policy.act(policy, verbose), hidden

  def train(self, experiences,
            batch_steps=1,
            train=True,
            log=True,
            zipped=False,
            retrieve_kls=False, 
            **kwargs):
    if not zipped:
      experiences = util.deepZip(*experiences)
    
    input_dict = dict(util.deepValues(util.deepZip(self.experience, experiences)))
    
    """
    saved_data = self.sess.run(self.saved_data, input_dict)
    handles = [t.handle for t in saved_data]
    
    saved_dict = dict(zip(self.placeholders, handles))
    """
    
    run_dict = dict(
      global_step = self.global_step,
      misc = self.misc
    )
    
    if train:
      run_dict.update(train=self.train_ops)
    
    if retrieve_kls:
      run_dict.update(kls=self.kls)
    
    if self.profile:
      run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
      run_metadata = tf.RunMetadata()
      print('Profiling enabled, disabling logging!')
      log = False # logging eats time?
    else:
      run_options = None
      run_metadata = None

    if log:
      run_dict.update(summary=self.summarize)
    
    outputs = []
    
    for _ in range(batch_steps):
      try:
        results = self.sess.run(run_dict, input_dict,
            options=run_options, run_metadata=run_metadata)
      except tf.errors.InvalidArgumentError as e:
        import pickle
        with open(os.path.join(self.path, 'error_frame'), 'wb') as f:
          pickle.dump(experiences, f)
        raise e
      #print('After run: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      
      outputs.append(results)
      global_step = results['global_step']
      if log:
        summary_str = results['summary']
        self.writer.add_summary(summary_str, global_step)
      if self.profile:
        # Create the Timeline object, and write it to a json
        from tensorflow.python.client import timeline
        tl = timeline.Timeline(run_metadata.step_stats)
        ctf = tl.generate_chrome_trace_format()
        path = 'timelines/%s' % self.name
        util.makedirs(path)
        with open('%s/%d.json' % (path, global_step), 'w') as f:
          f.write(ctf)
        #self.writer.add_run_metadata(run_metadata, 'step %d' % global_step, global_step)
    
    return outputs

  # save weights to disk
  def save(self):
    util.makedirs(self.path)
    print("Saving to", self.path)
    self.saver.save(self.sess, self.snapshot_path, write_meta_graph=False)

  # restore weights from disk
  def restore(self, path=None):
    if path is None:
      path = self.snapshot_path
    print("Restoring from", path)
    self.saver.restore(self.sess, path)

  # initializes weights
  def init(self):
    self.sess.run(self.initializer)
  
  # for learner agent to call, to serialize itself to send to actors 
  def blob(self):
    with self.graph.as_default():
      values = self.sess.run(self.variables)
      return {var.name: val for var, val in zip(self.variables, values)}
  
  # for actors to call, to unserialize updated weights from learners. 
  def unblob(self, blob):
    #self.sess.run(self.unblobber, {self.placeholders[k]: v for k, v in blob.items()})
    self.sess.run(self.unblobber, {v: blob[k] for k, v in self.placeholders.items()})

