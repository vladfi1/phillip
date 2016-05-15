import tensorflow as tf
import ssbm
import tf_lib as tfl
import numpy as np
from numpy import random, exp
import RL

def flip(p):
    return random.binomial(1, p)

class Agent:
    def __init__(self, model, path, reload_every=60*60, seed=None):
        self.model = RL.Model(model, path)
        self.reload_every = reload_every
        self.counter = 0
        self.simple_controller = ssbm.simpleControllerStates[0]
        self.model.restore()

        if seed is not None:
            random.seed(seed)

    def act(self, state, pad):
        action = self.model.act(state)
        self.simple_controller = ssbm.SimpleControllerState.fromIndex(action)

        if self.counter % 60 == 0:
            print(state.players[1])
            #print("Probs", probs)
            print(self.simple_controller)

        pad.send_controller(self.simple_controller.realController())

        self.counter += 1

        if self.counter >= self.reload_every:
            self.model.restore()
            self.counter = 0

