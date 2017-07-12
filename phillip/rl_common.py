import tensorflow as tf
from .default import *

class RLConfig(Default):
  _options = [
    Option('tdN', type=int, default=5, help="use n-step TD error"),
    Option('reward_halflife', type=float, default=2.0, help="time to discount rewards by half, in seconds"),
    Option('act_every', type=int, default=3, help="Take an action every ACT_EVERY frames."),
    #Option('experience_time', type=int, default=1, help="Length of experiences, in seconds."),
    Option('experience_length', type=int, default=30, help="Length of experiences, in frames."),
    Option('delay', type=int, default=0, help="frame delay on actions taken"),
    Option('memory', type=int, default=0, help="number of frames to remember"),
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    self.fps = 60 // self.act_every
    self.discount = 0.5 ** ( 1.0 / (self.fps*self.reward_halflife) )
    #self.experience_length = self.experience_time * self.fps

def makeHistory(state, prev_action, memory=0, **unused):
  combined = tf.concat(axis=2, values=[state, prev_action])
  #length = tf.shape(combined)[-2] - memory
  length = combined.get_shape()[-2].value - memory
  history = [tf.slice(combined, [0, i, 0], [-1, length, -1]) for i in range(memory+1)]
  return tf.concat(axis=2, values=history)

