import tensorflow as tf
import ssbm
import tf_lib as tfl
import numpy as np
from numpy import random, exp
import RL
import util

class Agent:
  def __init__(self,
               model=None,
               path=None,
               reload_every=60*60,
               swap=False,
               memory=0,
               delay=0,
               **kwargs):
    self.model = RL.Model(model, path, swap=swap, mode=RL.Mode.PLAY, memory=memory, **kwargs)
    self.reload_every = reload_every
    self.counter = 0
    self.action = 0
    self.actions = util.CircularQueue(delay+1, 0)
    self.memory = util.CircularQueue(array=((memory+1) * ssbm.SimpleStateAction)())
    self.model.restore()

  def act(self, state, pad):
    #verbose = self.counter % 60 == 0
    verbose = False
    
    current = self.memory.peek()
    current.state = state
    
    self.memory.increment()
    history = self.memory.as_list()
    
    self.prev_action = self.action
    current.prev_action = self.prev_action
    
    self.action = self.model.act(history, verbose)
    current.action = self.action

    if verbose:
      print(state.players[1])
      print(self.action)
    
    # the delayed action
    action = self.actions.push(self.action)

    controller = ssbm.simpleControllerStates[action]
    pad.send_controller(controller.realController())

    self.counter += 1

    if self.counter % self.reload_every == 0:
      self.model.restore()

