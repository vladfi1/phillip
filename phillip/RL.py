import os
import tensorflow as tf
import numpy as np
from enum import Enum
from . import ssbm, tf_lib as tfl, util, embed, ctype_util as ct
from .default import Default, Option
from .rl_common import *
from .dqn import DQN
from .ac import ActorCritic
from .rac import RecurrentActorCritic
from .rdqn import RecurrentDQN
from .critic import Critic
from .model import Model

#import resource

class Mode(Enum):
  TRAIN = 0
  PLAY = 1

policies = [
  DQN,
  ActorCritic,
  #ThompsonDQN,
  RecurrentActorCritic,
  RecurrentDQN,
]
policies = {policy.__name__ : policy for policy in policies}

class RL(Default):
  _options = [
    Option('policy', type=str, default="ActorCritic", choices=policies.keys()),
    Option('path', type=str, help="path to saved policy"),
    Option('gpu', action="store_true", default=False, help="run on gpu"),
    Option('action_type', type=str, default="diagonal", choices=ssbm.actionTypes.keys()),
    Option('name', type=str),
    Option('train_model', type=int, default=0),
    Option('train_policy', type=int, default=1),
    Option('train_critic', type=int, default=1),
    Option('predict', type=int, default=0),
    Option('profile', type=int, default=0, help='profile tensorflow graph execution'),
    Option('save_cpu', type=int, default=0),
  ]
  
  _members = [
    ('config', RLConfig),
    ('embedGame', embed.GameEmbedding),
    ('critic', Critic),
    ('model', Model),
    #('opt', Optimizer),
  ]
  
  def __init__(self, mode = Mode.TRAIN, debug = False, **kwargs):
    Default.__init__(self, init_members=False, **kwargs)
    self.config = RLConfig(**kwargs)
    
    if self.name is None:
      self.name = self.policy
    
    if self.path is None:
      self.path = "saves/%s/" % self.name
    
    self.snapshot = os.path.join(self.path, 'snapshot')
    
    policyType = policies[self.policy]
    self.actionType = ssbm.actionTypes[self.action_type]
    embedAction = embed.OneHotEmbedding("action", self.actionType.size)

    self.graph = tf.Graph()
    
    device = '/gpu:0' if self.gpu else '/cpu:0'
    print("Using device " + device)
    
    if not self.gpu:
      os.environ['CUDA_VISIBLE_DEVICES'] = ""
    
    with self.graph.as_default(), tf.device(device):
      self.global_step = tf.Variable(0, name='global_step', trainable=False)
      
      self.embedGame = embed.GameEmbedding(**kwargs)
      state_size = self.embedGame.size
      combined_size = state_size + embedAction.size
      history_size = (1+self.config.memory) * combined_size
      print("History size:", history_size)

      self.components = {}
      
      if self.predict or (mode == Mode.TRAIN and self.train_model):
        print("Creating model.")
        self.model = Model(self.embedGame, embedAction.size, self.config, **kwargs)
        self.components['model'] = self.model

      if mode == Mode.PLAY or self.train_policy:
        print("Creating policy:", self.policy)

        effective_delay = self.config.delay
        if self.predict:
          effective_delay -= self.model.predict_steps
        input_size = history_size + effective_delay * embedAction.size
        self.policy = policyType(input_size, embedAction.size, self.config, **kwargs)
        self.components['policy'] = self.policy
      
      if mode == Mode.TRAIN:
        if self.train_policy or self.train_critic:
          print("Creating critic.")
          self.critic = Critic(history_size, **kwargs)
          self.components['critic'] = self.critic

        self.experience = ct.inputCType(ssbm.SimpleStateAction, [None, self.config.experience_length], "experience")
        # instantaneous rewards for all but the last state
        self.experience['reward'] = tf.placeholder(tf.float32, [None, self.config.experience_length-1], name='experience/reward')

        # manipulating time along the first axis is much more efficient
        # experience_swapped = util.deepMap(tf.transpose, self.experience)
        
        # initial state for recurrent networks
        #self.experience['initial'] = tuple(tf.placeholder(tf.float32, [None, size], name='experience/initial/%d' % i) for i, size in enumerate(self.policy.hidden_size))
        if self.train_policy:
          self.experience['initial'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [None, size], name="experience/initial"), self.policy.hidden_size)
        else:
          self.experience['initial'] = []

        states = self.embedGame(self.experience['state'])
        prev_actions = embedAction(self.experience['prev_action'])
        combined = tf.concat(axis=2, values=[states, prev_actions])
        actions = embedAction(self.experience['action'])

        memory = self.config.memory
        delay = self.config.delay
        length = self.config.experience_length - memory
        history = [combined[:,i:i+length] for i in range(memory+1)]

        actions = actions[:,memory:]
        rewards = self.experience['reward'][:,memory:]
        
        print("Creating train ops")

        with tf.variable_scope('train'):
          train_ops = []
          #losses = []
          #loss_vars = []
  
          if self.train_model or self.predict:
            train_model, predicted_history = self.model.train(history, actions, self.experience['state'])
          if self.train_model:
            train_ops.append(train_model)
            #losses.append(model_loss)
            #loss_vars.extend(self.model.getVariables())
          
          if self.train_policy or self.train_critic:
            train_critic, targets, advantages = self.critic(history, rewards)
          if self.train_critic:
            train_ops.append(train_critic)
          
          if self.train_policy:
            if self.predict:
              predict_steps = self.model.predict_steps
              history = predicted_history
            else:
              predict_steps = 0
  
            delayed_actions = []
            delay_length = length - delay
            for i in range(predict_steps, delay+1):
              delayed_actions.append(actions[:,i:i+delay_length])
            policy_args = dict(
              history=[h[:,:delay_length] for h in history],
              actions=delayed_actions,
              prob=self.experience['prob'][:,memory+delay:],
              advantages=advantages[:,delay:],
              targets=targets[:,delay:]
            )
            train_ops.append(self.policy.train(**policy_args))

          """
          total_loss = tf.add_n(losses)
          self.opt = Optimizer(**kwargs)
          op = self.opt.optimize(total_loss / self.opt.learning_rate)
          train_ops.append(op)
          """
          
        print("Created train op(s)")

        #tf.scalar_summary("loss", loss)
        #tf.scalar_summary('learning_rate', tf.log(self.learning_rate))
        
        tf.summary.scalar('reward', tf.reduce_mean(self.experience['reward']))
        
        self.summarize = tf.summary.merge_all()
        self.increment = tf.assign_add(self.global_step, 1)
        self.misc = tf.group(self.increment)
        self.train_ops = tf.group(*train_ops)
        
        print("Creating summary writer at logs/%s." % self.name)
        self.writer = tf.summary.FileWriter('logs/' + self.name)#, self.graph)
      else:
        # with tf.name_scope('policy'):
        self.input = ct.inputCType(ssbm.SimpleStateAction, [self.config.memory+1], "input")
        self.input['delayed_action'] = tf.placeholder(tf.int64, [self.config.delay], "delayed_action")
        self.input['hidden'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [size], name="input/hidden"), self.policy.hidden_size)

        states = self.embedGame(self.input['state'])
        prev_actions = embedAction(self.input['prev_action'])
        combined = tf.concat(axis=1, values=[states, prev_actions])
        history = tf.unstack(combined)
        actions = embedAction(self.input['delayed_action'])
        
        if self.predict:
          predict_actions = actions[:self.model.predict_steps]
          delayed_actions = actions[self.model.predict_steps:]
          history = self.model.predict(history, predict_actions, self.input['state'])
        else:
          delayed_actions = actions
        
        self.run_policy = self.policy.getPolicy(history, delayed_actions)
      
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

  def get_global_step(self):
    return self.sess.run(self.global_step)

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    return self.policy.act(self.sess.run(self.run_policy, feed_dict), verbose)

  def train(self, experiences, batch_steps=1, train=True, log=True, zipped=False, **kwargs):
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
      
      global_step = results['global_step']
      if log:
        print('add_summary')
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

  def save(self):
    util.makedirs(self.path)
    print("Saving to", self.path)
    self.saver.save(self.sess, self.snapshot, write_meta_graph=False)

  def restore(self):
    print("Restoring from", self.path)
    self.saver.restore(self.sess, self.snapshot)

  def init(self):
    self.sess.run(self.initializer)
  
  def blob(self):
    with self.graph.as_default():
      values = self.sess.run(self.variables)
      return {var.name: val for var, val in zip(self.variables, values)}
  
  def unblob(self, blob):
    #self.sess.run(self.unblobber, {self.placeholders[k]: v for k, v in blob.items()})
    self.sess.run(self.unblobber, {v: blob[k] for k, v in self.placeholders.items()})

