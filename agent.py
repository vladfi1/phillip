import tensorflow as tf
import ssbm
import tf_lib as tfl
import numpy as np
from numpy import random, exp
import RL
import util
from default import *
from menu_manager import characters
import ctype_util as ct
import pprint

pp = pprint.PrettyPrinter(indent=2)

class Agent(Default):
  _options = [
    Option('delay', type=int, default=0, help="delay actions this many rounds"),
    Option('char', type=str, choices=characters.keys(), help="character that this agent plays as"),
    Option('verbose', action="store_true", default=False, help="print stuff while running"),
  ]
  
  _members = [
    ('model', RL.Model)
  ]
  
  def __init__(self, reload_every=None, **kwargs):
    kwargs = kwargs.copy()
    kwargs.update(mode=RL.Mode.PLAY)
    Default.__init__(self, **kwargs)
    
    self.reload_every = reload_every
    
    self.counter = 0
    self.action = 0
    self.actions = util.CircularQueue(self.delay+1, 0)
    self.memory = util.CircularQueue(array=((self.model.memory+1) * ssbm.SimpleStateAction)())
    
    self.hidden = list(map(np.zeros, self.model.model.hidden_size))
    
    self.model.restore()

  def act(self, state, pad):
    verbose = self.verbose and (self.counter % (10 * self.model.rlConfig.fps) == 0)
    #verbose = False
    
    current = self.memory.peek()
    current.state = state
    
    self.prev_action = self.action
    current.prev_action = self.prev_action

    self.memory.increment()
    history = self.memory.as_list()
    
    history = ct.vectorizeCTypes(ssbm.SimpleStateAction, history)
    history['hidden'] = self.hidden
    
    self.action, self.hidden = self.model.act(history, verbose)
    
    current.action = self.action

    if verbose:
      pp.pprint(ct.toDict(state.players[1]))
      print(self.action)
    
    # the delayed action
    action = self.actions.push(self.action)

    # TODO: make the banned action system more robust
    
    # prevent peach from using toad
    # for some reason it causes both agents to use action 0
    if self.char == 'peach' and action == 22:
      action = 4
    
    # prevent sheik and zelda from transforming
    if self.char in ['zelda', 'sheik'] and action in [18, 21, 24]:
      action = 4

    controller = ssbm.simpleControllerStates[action]
    pad.send_controller(controller.realController())

    self.counter += 1

    if self.reload_every and self.counter % self.reload_every == 0:
      self.model.restore()

