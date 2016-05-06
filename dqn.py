import tensorflow as tf
import tf_lib as tfl
import util

class DQN:
  def __init__(self, state_size, action_size):
    self.state_size = state_size
    self.action_size = action_size

    layer_sizes = [state_size + action_size, 128, 128]
    self.layers = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu)
      for prev, next in zip(layer_sizes[:-1], layer_sizes[1:])]
    self.layers.append(util.compose(tf.squeeze, tfl.makeAffineLayer(layer_sizes[-1], 1)))

  def getQValues(self, state, action):
    embedded_input = tf.concat(1, [state, action])
    outputs = [embedded_input]
    for i, f in enumerate(self.layers):
      with tf.name_scope('q%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getLoss(self, states, actions, rewards):
    qs = self.getQValues(states, actions)
    qOut = qs[-1]

    qLosses = tf.squared_difference(qs[-1], rewards)
    qLoss = tf.reduce_mean(qLosses)
    return qLoss
