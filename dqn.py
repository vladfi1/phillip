import tensorflow as tf
import tf_lib as tfl
import util

class DQN:
  def __init__(self, input_size, action_size):
    self.input_size = input_size
    self.action_size = action_size

    layer_sizes = [input_size, 128, 128]
    self.layers = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu)
      for prev, next in zip(layer_sizes[:-1], layer_sizes[1:])]

    mu = util.compose(tf.squeeze, tfl.makeAffineLayer(layer_sizes[-1], 1))
    log_sigma2 = util.compose(tf.squeeze, tfl.makeAffineLayer(layer_sizes[-1], 1))
    self.layers.append(lambda x: (mu(x), log_sigma2(x)))

  def getQLayers(self, state):
    outputs = [state]
    for i, f in enumerate(self.layers):
      with tf.name_scope('q%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getQValues(self, state):
    return self.getQLayers(state)[-1]

  def getSquaredQLoss(self, states, rewards):
    mu, _ = self.getQValues(states)

    qLosses = tf.squared_difference(mu, rewards)
    qLoss = tf.reduce_mean(qLosses)
    return qLoss

  def getNLLQLoss(self, states, rewards):
    "Negative Log-Likelihood"
    mu, log_sigma2 = self.getQValues(states)
    nll = tf.squared_difference(mu, rewards) * tf.exp(-log_sigma2) + log_sigma2
    return tf.reduce_mean(nll)
