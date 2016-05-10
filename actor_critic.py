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

def getDiscoutFactor(reward_halflife = 2.0):
  fps = 60.0 / 5.0
  return 0.5 ** ( 1.0 / (fps*reward_halflife) )

discount_factor = getDiscoutFactor()

class ActorCritic:
  def __init__(self, state_size, action_size):
    self.state_size = state_size
    self.action_size = action_size

    shared_layer_sizes = [state_size, 128, 128]
    self.shared_layers = []
    # self.shared_layers = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu)
    #   for prev, next in zip(shared_layer_sizes[:-1], shared_layer_sizes[1:])]

    self.actor = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu)
      for prev, next in zip(shared_layer_sizes[:-1], shared_layer_sizes[1:])] + [
        tfl.makeAffineLayer(shared_layer_sizes[-1], action_size, tfl.leaky_relu),
        tfl.makeSplitLayer([5, 2]),
        [
          tfl.makeSoftmaxLayer('stick'),
          tfl.makeSoftmaxLayer('A'),
        ]
      ]

    self.critic = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu) for prev, next in zip(shared_layer_sizes[:-1], shared_layer_sizes[1:])] + [util.compose(
        tf.squeeze,
        tfl.makeAffineLayer(shared_layer_sizes[-1], 1))]


  def getActionDist(self, state):
    epsilon = 1e-5
    return getOutput(self.shared_layers + self.actor, state) + epsilon

  def getValue(self, state):
    return getOutput(self.shared_layers + self.critic, state)

  def getLoss(self, states, actions, returns, rewards):
    vOuts = self.getValue(states)

    vLosses = tf.squared_difference(vOuts, returns)
    vLoss = tf.reduce_mean(vLosses)

    action_probs = self.getActionDist(states)

    log_action_probs = tf.log(action_probs)
    # entropy = - tf.reduce_sum(action_probs * log_action_probs, 1)
    # v_shape = tf.shape(vOuts)
    # import ipdb; ipdb.set_trace()
    # v_shape[0] = v_shape[0] -
    # v_shape[1] = 0
    # last_v = tf.slice(vOuts,
                      # v_shape,
                      # [-1, -1])
    # padded_vOuts = tf.concat(0,[vOuts, last_v])
    # padded_vOuts = tf.stop_gradient(padded_vOuts)

    entropy = - tf.reduce_sum(action_probs * log_action_probs, 1)/2


    vOut_next = tf.pad(vOuts[1:], [[0, 1]], "SYMMETRIC")
    # vOuts = tf.Print(vOuts, [vOuts], message="vOuts")
    # vOut_next = tf.Print(vOut_next, [vOut_next], message="vOut_next")
    # vOut_next = tf.Print(vOut_next, [vOut_next], message="vOut_next")
    # vOut_current = tf.slice(vOuts, [0], tf.shape(vOuts) - 1)
    one_step_advantages = (rewards
                           + discount_factor * vOut_next
                           - vOuts)
    one_step_advantages = tf.stop_gradient(one_step_advantages)

    sum_log_action_probs = tf.reduce_sum(actions * log_action_probs, 1)


    self.aLosses = sum_log_action_probs * one_step_advantages - 0.01 * entropy
    aLoss = tf.reduce_mean(self.aLosses)

    aLoss = - aLoss # this gradient is in the direction of increasing reward
    return (vLoss, aLoss)
