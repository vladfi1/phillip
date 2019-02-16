import math
import tensorflow as tf
from phillip.RL import RL
from . import ssbm, util, ctype_util as ct, embed
from .core import Core
from .ac import ActorCritic
from .critic import Critic
from phillip import tf_lib as tfl
from .mutators import relative
from .default import Option
from phillip import reward
import os

class Learner(RL):
  
  _options = RL._options + [
    Option('train_model', type=int, default=0),
    Option('train_policy', type=int, default=1),
    # in theory train_critic should always equal train_policy; keeping them
    # separate might help for e.g. debugging
    Option('train_critic', type=int, default=1),
    Option('reward_decay', type=float, default=1e-3),
    Option('learning_rate', type=float, default=1e-4),
    Option('adam_epsilon', type=float, default=1e-8, help="epsilon for adam optimizer"),
    Option('adam_beta1', type=float, default=0.9, help="Adam momentum decay"),
    Option('clip_max_grad', type=float, default=1.),
    Option('evolve_learning_rate', action="store_true", help="false by default; if true, then" \
      "the learning rate is included in PBT among the things that get mutated. "),
    Option('explore_scale', type=float, default=0., help='use prediction error as additional reward'),
    Option('evolve_explore_scale', action="store_true", help='evolve explore_scale with PBT'),
    Option('unshift_critic', action='store_true', help="don't shift critic forward in time"),
    Option('batch_size', type=int),
    Option('neg_reward_scale', type=float, default=1., help="scale down negative rewards for more optimism"),
    Option('unpredict_weight', type=float, default=0., help="regress delayed actions (computed with prediction) to the undelayed ones (computed on true states)"),

    Option('damage_ratio', type=float, default=0.01, help="damage scale vs stocks"),
    Option('distance_scale', type=float, default=0., help="distance pseudo-reward"),
    Option('action_state_entropy_scale', type=float, default=0, help="reward unusual action states"),
  ]

  def __init__(self, debug=False, **kwargs):
    super(Learner, self).__init__(**kwargs)

    with self.graph.as_default(), tf.device(self.device): 
      # initialize predictive model, if either: 
      #  * you want to use the predictive model to "undo delay"
      #  * you want a predictive model to help you explore
      # note: self.predict is perhaps a misnomer. 
      if self.predict or (self.train_model or self.explore_scale):
        self._init_model(**kwargs)

      if self.train_policy: 
        self._init_policy(**kwargs)
      
      # build computation graph
      losses = {}

      # to train the the policy, you have to train the critic. (self.train_policy and 
      # self.train_critic might both be false, if we're only training the predictive
      # model)
      if self.train_policy or self.train_critic:
        print("Creating critic.")
        self.critic = Critic(self.core.output_size, **kwargs)

      # experience = trajectory. usually a list of SimpleStateAction's. 
      self.experience = ct.inputCType(ssbm.SimpleStateAction, [None, self.config.experience_length], "experience")
      # instantaneous rewards for all but the last state
      self.experience['reward'] = tf.placeholder(tf.float32, [None, self.config.experience_length-1], name='experience/reward')
      # manipulating time along the first axis is much more efficient
      experience = util.deepMap(tf.transpose, self.experience)       
      # initial state for recurrent networks
      self.experience['initial'] = tuple(tf.placeholder(tf.float32, [None, size], name='experience/initial/%d' % i) for i, size in enumerate(self.core.hidden_size))
      experience['initial'] = self.experience['initial']

      # auxiliary reward computation
      
      # rewards = experience['reward']
      # TODO: move these into reward.py?
      kill_death = reward.compute_rewards(experience['state'], damage_ratio=0., lib=tf)
      tfl.stats(kill_death * self.config.fps * 60, 'kill_death')
      
      rewards = reward.compute_rewards(experience['state'], damage_ratio=self.damage_ratio, lib=tf)
      avg_reward, _ = tfl.stats(rewards, 'reward')

      # distance rewards encourage agents to interact more
      distances, distance_rewards = reward.pseudo_rewards(experience['state'], reward.distance, 1., lib=tf)
      tfl.stats(distances, 'distances')
      tfl.stats(distance_rewards, 'distance_rewards')
      rewards += self.distance_scale * distance_rewards

      # action_state_entropy encourages agent to explore new action states
      own_action_states = experience['state']['players'][1]['action_state']
      
      action_state_logits = tf.Variable(tf.zeros([embed.numActions]), name="action_state_logits")
      broadcast_zeros = tf.expand_dims(tf.zeros_like(own_action_states, dtype=tf.float32), -1)  # [T, B, 1]
      expanded_action_state_logits = action_state_logits + broadcast_zeros  # [T, B, A]

      action_state_loss = tf.nn.sparse_softmax_cross_entropy_with_logits(
        logits=expanded_action_state_logits, labels=own_action_states)

      # don't need to scale because it is independent of the other losses
      losses['global_action_state'] = tf.reduce_mean(action_state_loss)
      tf.summary.scalar('action_state_loss', losses['global_action_state'])

      action_state_value = tf.minimum(action_state_loss, math.log(embed.numActions) + 2)
      action_state_rewards = action_state_value[1:] - action_state_value[:-1]
      rewards += self.action_state_entropy_scale * action_state_rewards
      tfl.stats(action_state_rewards, 'action_state_rewards')

      action_state_entropy = -tf.reduce_sum(
        tf.nn.softmax(action_state_logits) *
        tf.nn.log_softmax(action_state_logits))
      tf.summary.scalar('action_state_entropy', action_state_entropy)

      # main RL training here

      states = self.embedGame(experience['state'])
      prev_actions = self.embedAction(experience['prev_action'])
      combined = tf.concat(axis=2, values=[states, prev_actions])
      actions = self.embedAction(experience['action'])

      memory = self.config.memory
      delay = self.config.delay
      length = self.config.experience_length - memory
      history = [combined[i:i+length] for i in range(memory+1)]
      inputs = tf.concat(axis=-1, values=history)
      
      # this should be handled by the core itself
      if self.core.core:
        inputs = self.core.trunk(inputs)
        def f(prev, current_input):
          _, prev_state = prev
          return self.core.core(current_input, prev_state)
        batch_size = tf.shape(self.experience['reward'])[0]
        dummy_output = tf.zeros(tf.stack([batch_size, tf.constant(self.core.output_size)]))
        scan_fn = tf.scan if self.dynamic else tfl.scan
        core_outputs, hidden_states = scan_fn(f, inputs, (dummy_output, experience['initial']))
      else:
        core_outputs, hidden_states = self.core(inputs, experience['initial'])

      actions = actions[memory:]
      rewards = rewards[memory:]
      
      print("Creating train ops")

      train_ops = []
      loss_vars = []

      if self.train_model or self.predict:
        model_loss, predicted_core_outputs = self.model.train(history, core_outputs, hidden_states, actions, experience['state'])
      if self.train_model:
        #train_ops.append(train_model)
        losses['model'] = model_loss
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
        for i in range(predict_steps, delay):
          delayed_actions.append(actions[i:i+delay_length])
        taken_actions = experience['action'][memory+delay:]
        train_probs, train_log_probs, entropy = self.policy.train_probs(actor_inputs, delayed_actions, taken_actions)
        
        behavior_probs = experience['prob'][memory+delay:] # these are the actions we can compute probabilities for
        prob_ratios = tf.minimum(train_probs / behavior_probs, 1.)
        self.kls = -tf.reduce_mean(tf.log(prob_ratios), 0)
        tfl.stats(self.kls, 'kl')
      else:
        prob_ratios = tf.ones_like() # todo

      if self.explore_scale:
        if self.evolve_explore_scale:
          self.explore_scale = tf.Variable(self.explore_scale, trainable=False, name='explore_scale')
          self.evo_variables.append(('explore_scale', self.explore_scale, relative(1.5)))
        
        distances, _ = self.model.distances(history, core_outputs, hidden_states, actions, experience['state'], predict_steps=1)
        distances = tf.add_n(list(util.deepValues(distances))) # sum over different state components
        explore_rewards = self.explore_scale * distances[0]
        explore_rewards = tf.stop_gradient(explore_rewards)
        tfl.stats(explore_rewards, 'explore_rewards')
        rewards += explore_rewards

      # build the critic (which you'll also need to train the policy)
      if self.train_policy or self.train_critic:
        shifted_core_outputs = core_outputs[:delay_length] if self.unshift_critic else core_outputs[delay:]
        delayed_rewards = rewards[delay:]
        delayed_rewards = tf.nn.relu(delayed_rewards) - self.neg_reward_scale * tf.nn.relu(-delayed_rewards)
        critic_loss, targets, advantages = self.critic(shifted_core_outputs, delayed_rewards, prob_ratios[:-1])
      
      if self.train_critic:
        losses['critic'] = critic_loss
        loss_vars.extend(self.critic.variables)
      
      if self.train_policy:
        policy_loss = self.policy.train(train_log_probs[:-1], advantages, entropy[:-1])
        losses['policy'] = policy_loss
        loss_vars.extend(self.policy.getVariables())
        
        if self.unpredict_weight:
          true_states = core_outputs[predict_steps:]
          true_probs = self.policy.get_probs(true_states, delayed_actions)
          true_probs = tf.stop_gradient(true_probs)  # these are supervised targets
          # some redundancy here with train_probs
          predicted_probs = self.policy.get_probs(actor_inputs, delayed_actions)
          unpredict_kl = tfl.batch_dot(tf.log(true_probs) - tf.log(predicted_probs), true_probs)
          unpredict_kl = tf.reduce_mean(unpredict_kl)
          tf.summary.scalar('unpredict_kl', unpredict_kl)
          losses['unpredict'] = self.unpredict_weight * unpredict_kl

      if self.evolve_learning_rate:
        self.learning_rate = tf.Variable(self.learning_rate, trainable=False, name='learning_rate')
        self.evo_variables.append(('learning_rate', self.learning_rate, relative(1.5)))

      # losses = {k: tf.check_numerics(v, k, "check_"+k) for k, v in losses.items()}
      total_loss = tf.add_n(list(losses.values()))
      with tf.variable_scope('train'):
        optimizer = tf.train.AdamOptimizer(self.learning_rate, epsilon=self.adam_epsilon, beta1=self.adam_beta1)
        gvs = optimizer.compute_gradients(total_loss)
        gvs = [(tf.check_numerics(g, v.name), v) for g, v in gvs]
        gs, vs = zip(*gvs)
        
        norms = tf.stack([tf.norm(g) for g in gs])
        max_norm = tf.reduce_max(norms)
        tf.summary.scalar('max_grad_norm', max_norm)
        capped_gs = [tf.clip_by_norm(g, self.clip_max_grad) for g in gs]
        train_op = optimizer.apply_gradients(zip(capped_gs, vs))
        train_ops.append(train_op)
      
      print("Created train op(s)")
      
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
      self.num_steps_per_batch = self.batch_size * self.config.experience_length * self.config.act_every
      misc_ops.append(tf.assign_add(self.global_step, self.num_steps_per_batch))
      self.misc = tf.group(*misc_ops)
      self.train_ops = tf.group(*train_ops)

      print("Creating summary writer at logs/%s." % self.name)
      #self.writer = tf.summary.FileWriter('logs/' + self.name)#, self.graph)
      self.writer = tf.summary.FileWriter(self.path)

      self._finalize_setup()

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
