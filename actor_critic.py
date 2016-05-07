import tensorflow as tf
import tf_lib as tfl
import util

def getOutput(layers, x):
  if len(layers) == 0:
    return x
  elif type(layers[0]) == list:
    return getOutput(
                     layers[1:],
                     tf.concat(
                       1,
                       [getOutput([l], x_i) for (l, x_i) in zip(layers[0], x)]))
  else:
    return getOutput(layers[1:], layers[0](x))


class ActorCritic:
  def __init__(self, state_size, action_size):
    self.state_size = state_size
    self.action_size = action_size

    shared_layer_sizes = [state_size, 128, 128]
    self.shared_layers = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu)
      for prev, next in zip(shared_layer_sizes[:-1], shared_layer_sizes[1:])]

    self.actor = [
        tfl.makeAffineLayer(shared_layer_sizes[-1], action_size, tfl.leaky_relu),
        tfl.makeSplitLayer([5, 2]),
        [
          tfl.makeSoftmaxLayer('stick'),
          tfl.makeSoftmaxLayer('A'),
        ]
      ]

    self.critic = [util.compose(
        tf.squeeze,
        tfl.makeAffineLayer(shared_layer_sizes[-1], 1))]


  def getActionDist(self, state):
    return getOutput(self.shared_layers + self.actor, state)

  def getValue(self, state):
    return getOutput(self.shared_layers + self.critic, state)

  def getLoss(self, states, actions, rewards):
    vOuts = self.getValue(states)

    vLosses = tf.squared_difference(vOuts, rewards)
    vLoss = tf.reduce_mean(vLosses)

    action_probs = self.getActionDist(states)
    log_action_probs = tf.log(action_probs)
    advantages = tf.stop_gradient(vOuts - rewards) # this way is victory
    # advantages = tf.stop_gradient(rewards - vOuts) # this way is death


    # n_examples = rewards.get_shape()[0].value
    # import ipdb; ipdb.set_trace()
    aLosses = actions * action_probs * tf.reshape(advantages, [-1, 1])
    aLoss = tf.reduce_mean(aLosses)

    return vLoss + 10 * aLoss
