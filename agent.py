import tensorflow as tf
import ssbm
import tf_lib as tfl
import numpy as np
from numpy import random, exp
import RL

def flip(p):
  return random.binomial(1, p)

class Agent:
  def __init__(self, model=None, path=None, reload_every=60*60, swap=False, **kwargs):
    self.model = RL.Model(model, path, swap=swap, mode=RL.Mode.PLAY, **kwargs)
    self.reload_every = reload_every
    self.counter = 0
    self.simple_controller = ssbm.simpleControllerStates[0]
    self.model.restore()

  def act(self, state, pad):
    verbose = self.counter % 60 == 0
    action = self.model.act(state, verbose)
    self.simple_controller = ssbm.SimpleControllerState.fromIndex(action)

    if verbose:
      print(state.players[1])
      print(self.simple_controller)

    pad.send_controller(self.simple_controller.realController())

    self.counter += 1

    if self.counter >= self.reload_every:
      self.model.restore()
      self.counter = 0

