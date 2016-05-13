import tensorflow as tf
import tf_lib as tfl
import util

class ActorCritic:
  def __init__(self, input_size, action_size):
    self.input_size = input_size
    self.action_size = action_size

    layer_sizes = [input_size, 128, 128]
    self.layers = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu)
      for prev, next in zip(layer_sizes[:-1], layer_sizes[1:])]

    v = tfl.makeAffineLayer(layer_sizes[-1], 1)
    actor = tfl.makeAffineLayer(layer_sizes[-1], action_size)

    self.layers.append(lambda x: (tf.squeeze(v(x)), actor(x)))

  def getLayers(self, state):
    outputs = [state]
    for i, f in enumerate(self.layers):
      with tf.name_scope('q%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getOutput(self, state):
    return self.getLayers(state)[-1]
