"""
Abstract base class. (If that's a thing in Python?) Should never be 
publicly exported. 
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
  
  def __init__(self, debug, **kwargs):
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
    self.embedAction = embed.OneHotEmbedding("action", self.actionType.size)
    
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
    self.saver.restore(self.sess, path)

  # initializes weights
  def init(self):
    self.sess.run(self.initializer)