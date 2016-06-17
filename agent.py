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
    self.model = RL.Model(model, path, swap=swap, mode=RL.Mode.PLAY, **kwargs)
    self.reload_every = reload_every
    self.counter = 0
    self.action = 0
    self.queue = util.CircularQueue(delay+1, init=0)
    self.model.restore()

  def act(self, state, pad):
    verbose = self.counter % 60 == 0
    
    self.prev_action = self.action
    self.action = self.model.act(state, self.prev_action, verbose)
    self.queue.push(self.action)

    if verbose:
      print(state.players[1])
      print(self.action)

    controller = ssbm.simpleControllerStates[self.queue.peek()]
    pad.send_controller(controller.realController())

    self.counter += 1

    if self.counter >= self.reload_every:
      self.model.restore()
      self.counter = 0

