"""
Parent RL class for Actor and Learner. 
"""

import os
import tensorflow as tf
import numpy as np
from enum import Enum
from . import ssbm, tf_lib as tfl, util, embed
from .default import Default, Option
from .rl_common import *
from .ac import ActorCritic
from .critic import Critic
from .model import Model
from .core import Core

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
    Option('profile', type=int, default=0, help='profile tensorflow graph execution'),
    Option('save_cpu', type=int, default=0),
    Option('evolve', action="store_true", help="are we part of an evolving population"),
    Option('pop_id', type=int, default=-1, help="If pop_id >= 0, then we're doing" \
      "population-based training, and pop_id tracks the worker's id. Else we're not" \
      "doing PBT and the id is -1."), 
    Option('dynamic', type=int, default=1, help='use dynamic loop unrolling'),
    Option('action_space_embed', type=int, default=0, help='embed actions'),
  ]
  
  _members = [
    ('config', RLConfig),
    ('embedGame', embed.GameEmbedding),
    ('critic', Critic),
    ('model', Model),
    ('core', Core),
    #('opt', Optimizer),
    ('policy', ActorCritic),
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, init_members=False, **kwargs)
    self.config = RLConfig(**kwargs)
    
    if self.name is None: self.name = "ActorCritic"
    if self.path is None: self.path = "saves/%s/" % self.name
    # the below is a hack that makes it easier to run phillip from the command
    # line, if we're doing PBT but don't want to specify the population ID. 
    if self.evolve and self.pop_id < 0: self.pop_id = 0
    if self.pop_id >= 0:
      self.root = self.path
      self.path = os.path.join(self.path, str(self.pop_id))
      print(self.path)
    # where trained agents get saved onto disk. 
    self.snapshot_path = os.path.join(self.path, 'snapshot')
    self.actionType = ssbm.actionTypes[self.action_type]

    self.graph = tf.Graph()
    self.device = '/gpu:0' if self.gpu else '/cpu:0'
    print("Using device " + self.device)
    with self.graph.as_default(), tf.device(self.device):
      if self.action_space_embed:
        self.embedAction = embed.LookupEmbedding('action', self.actionType.size, self.action_space_embed)
      else:
        # takes in action, and returns a one-hot vector corresponding to that action.
        self.embedAction = embed.OneHotEmbedding("action", self.actionType.size)

      # total number of gradient descent steps the learner has taken thus far
      self.global_step = tf.Variable(0, name='global_step', dtype=tf.int64, trainable=False)
      self.evo_variables = []
      
      self.embedGame = embed.GameEmbedding(**kwargs)
      state_size = self.embedGame.size
      combined_size = state_size + self.embedAction.size
      history_size = (1+self.config.memory) * combined_size
      print("History size:", history_size)

      self.core = Core(history_size, **kwargs)
      
    
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
    tfl.restore(self.sess, self.variables, path)
    # self.saver.restore(self.sess, path)

  # initializes weights
  def init(self):
    self.sess.run(self.initializer)

  # currently enables Learner to serialize itself to send to Actors 
  def blob(self):
    with self.graph.as_default():
      values = self.sess.run(self.variables)
      return {var.name: val for var, val in zip(self.variables, values)}

  # currently enables Actors to unserializing updated weights sent from a Learner
  def unblob(self, blob):
    #self.sess.run(self.unblobber, {self.placeholders[k]: v for k, v in blob.items()})
    self.sess.run(self.unblobber, {v: blob[k] for k, v in self.placeholders.items()})
  
  # helper methods for initialization
  def _init_model(self, **kwargs):
    print("Creating model.")
    self.model = Model(self.embedGame, self.embedAction.size, self.core, self.config, **kwargs)

  def _init_policy(self, **kwargs):
    effective_delay = self.config.delay
    if self.predict:
      effective_delay -= self.model.predict_steps
    input_size = self.core.output_size + effective_delay * self.embedAction.size
    
    self.policy = ActorCritic(input_size, self.embedAction, self.config, **kwargs)
    self.evo_variables.extend(self.policy.evo_variables)

  def _finalize_setup(self):
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
