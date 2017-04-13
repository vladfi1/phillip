import os
import tensorflow as tf
import numpy as np
from enum import Enum
import os
import random
from . import ssbm, tf_lib as tfl, util, embed, ctype_util as ct
import ctypes
from .default import *
from .rl_common import *
from .dqn import DQN
from .ac import ActorCritic
from .reward import computeRewards
from .rac import RecurrentActorCritic
from .rdqn import RecurrentDQN
from .critic import Critic
from .model import Model

import resource

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
  ]
  
  _members = [
    ('config', RLConfig),
    ('embedGame', embed.GameEmbedding),
    ('critic', Critic),
    ('model', Model),
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
      
      history_size = (1+self.config.memory) * (state_size+embedAction.size)
      print("History size:", history_size)
      
      print("Creating policy:", self.policy)
      self.policy = policyType(self.embedGame, embedAction, self.global_step, self.config, **kwargs)
      
      if self.train_model:
        self.model = Model(**kwargs)
      
      if mode == Mode.TRAIN:
        if self.train_policy or self.train_critic:
          self.critic = Critic(self.embedGame, embedAction, **kwargs)

        with tf.name_scope('train'):
          self.experience = ct.inputCType(ssbm.SimpleStateAction, [None, self.config.experience_length], "experience")
          # instantaneous rewards for all but the last state
          self.experience['reward'] = tf.placeholder(tf.float32, [None, self.config.experience_length-1], name='experience/reward')
          
          # initial state for recurrent networks
          #self.experience['initial'] = tuple(tf.placeholder(tf.float32, [None, size], name='experience/initial/%d' % i) for i, size in enumerate(self.policy.hidden_size))
          self.experience['initial'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [None, size], name="experience/initial"), self.policy.hidden_size)
          
          delay_length = self.config.experience_length - self.config.delay
          
          def process_experiences(f, keys):
            return {k: util.deepMap(f, self.experience[k]) for k in keys}

          with tf.name_scope('live'):
            #live = {k: util.deepMap(lambda t: t[:,:delay_length] for k in ['state', 'action', 'prev_action']}
            live = process_experiences(lambda t: t[:,:delay_length], ['state', 'action', 'prev_action'])
            live['initial'] = self.experience['initial']

          with tf.name_scope('delayed'):
            delayed = live.copy()
            delayed.update(process_experiences(lambda t: t[:,self.config.delay:], ['state', 'reward']))
          
          policy_args = live
          critic_args = delayed
          
          print("Creating train ops")
          
          train_ops = []
          
          if self.train_policy or self.train_critic:
            train_critic, targets, advantages = self.critic(**critic_args)
          
          if self.train_critic:
            train_ops.append(train_critic)
          
          if self.train_policy:
            policy_args.update(advantages=tf.stop_gradient(advantages), targets=targets)
            train_ops.append(self.policy.train(**policy_args))

          if self.train_model:
            train_ops.append(self.model.train(**delayed))
          
          print("Created train ops")

          #tf.scalar_summary("loss", loss)
          #tf.scalar_summary('learning_rate', tf.log(self.learning_rate))
          
          tf.scalar_summary('reward', tf.reduce_mean(self.experience['reward']))
          
          merged = tf.merge_all_summaries()
          
          increment = tf.assign_add(self.global_step, 1)
          
          misc = tf.group(increment)
          
          self.run_dict = dict(
            summary=merged,
            global_step=self.global_step,
            train=tf.group(*train_ops),
            misc=misc
          )
          
          print("Creating summary writer at logs/%s." % self.name)
          self.writer = tf.train.SummaryWriter('logs/' + self.name)#, self.graph)
      else:
        with tf.name_scope('policy'):
          self.input = ct.inputCType(ssbm.SimpleStateAction, [self.config.memory+1], "input")
          
          #self.input['hidden'] = [tf.placeholder(tf.float32, [size], name='input/hidden/%d' % i) for i, size in enumerate(self.policy.hidden_size)]
          self.input['hidden'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [size], name="input/hidden"), self.policy.hidden_size)
          
          states = self.embedGame(self.input['state'])
          prev_actions = embedAction(self.input['prev_action'])
          
          history = tf.concat(1, [states, prev_actions])
          history = tf.reshape(history, [history_size])
          
          policy_args = dict(
            hidden=self.input['hidden'],
            state=history,
          )
          
          self.run_policy = self.policy.getPolicy(**policy_args)
      
      self.debug = debug
      
      self.variables = tf.all_variables()
      self.initializer = tf.initialize_all_variables()
      
      self.saver = tf.train.Saver(self.variables)
      
      self.placeholders = {v.name : tf.placeholder(v.dtype, v.get_shape()) for v in self.variables}
      self.unblobber = tf.group(*[tf.assign(v, self.placeholders[v.name]) for v in self.variables])
      
      self.graph.finalize()
      
      tf_config = dict(
        allow_soft_placement=True,
        #log_device_placement=True,
      )
      
      if mode == Mode.PLAY: # don't eat up cpu cores
        tf_config.update(
          inter_op_parallelism_threads=1,
          intra_op_parallelism_threads=1,
        )
      else:
        tf_config.update(
          #gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.3),
        )
      
      self.sess = tf.Session(
        graph=self.graph,
        config=tf.ConfigProto(**tf_config),
      )

  def act(self, history, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, history)))
    return self.policy.act(self.sess.run(self.run_policy, feed_dict), verbose)

  def train(self, experiences, batch_steps=1, **kwargs):
    experiences = util.deepZip(*experiences)
    experiences = util.deepMap(np.array, experiences)
    
    input_dict = dict(util.deepValues(util.deepZip(self.experience, experiences)))
    
    """
    saved_data = self.sess.run(self.saved_data, input_dict)
    handles = [t.handle for t in saved_data]
    
    saved_dict = dict(zip(self.placeholders, handles))
    """

    if self.debug:
      self.debugGrads(input_dict)
    
    for _ in range(batch_steps):
      try:
        results = self.sess.run(self.run_dict, input_dict)
      except tf.errors.InvalidArgumentError as e:
        import pickle
        with open(self.path + 'error', 'wb') as f:
          pickle.dump(experiences, f)
        raise e
      #print('After run: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      
      summary_str = results['summary']
      global_step = results['global_step']
      self.writer.add_summary(summary_str, global_step)
      #print('After summary: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

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

