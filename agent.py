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
               delay=0,
               **kwargs):
    self.model = RL.Model(model, path, swap=swap, mode=RL.Mode.PLAY, delay=delay, **kwargs)
    self.reload_every = reload_every
    self.counter = 0
    self.action = 0
    self.delay = delay + 1
    self.queue = (self.delay * ssbm.SimpleStateAction)()
    self.model.restore()

  def act(self, state, pad):
    verbose = self.counter % 60 == 0
    
    self.prev_action = self.action
    
    index = self.counter % self.delay
    current = self.queue[index]
    
    current.state = state
    current.prev_action = self.prev_action
    
    index += 1
    index %= self.delay
    
    history = self.queue[index:] + self.queue[:index]
    
    self.action = self.model.act(history, verbose)
    current.action = self.action

    if verbose:
      print(state.players[1])
      print(self.action)

    controller = ssbm.simpleControllerStates[self.queue[index].action]
    pad.send_controller(controller.realController())

    self.counter += 1

    if self.counter % self.reload_every == 0:
      self.model.restore()

