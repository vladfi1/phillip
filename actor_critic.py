import tensorflow as tf
import tf_lib as tfl
import util
import config
from numpy import random

class ActorCritic:
  def __init__(self, state_size, action_size, global_step):
    self.action_size = action_size
    self.layer_sizes = [state_size, 128, 128]
    self.layers = []

    with tf.name_scope('epsilon'):
      #epsilon = tf.constant(0.02)
      self.epsilon = 0.04 + 0.5 * tf.exp(-tf.cast(global_step, tf.float32) / 50000.0)

    for i in range(len(self.layer_sizes)-1):
      prev_size = self.layer_sizes[i]
      next_size = self.layer_sizes[i+1]

      with tf.variable_scope("layer_%d" % i):
        self.layers.append(tfl.makeAffineLayer(prev_size, next_size, tfl.leaky_relu))

    with tf.variable_scope('value'):
      values = tfl.makeAffineLayer(self.layer_sizes[-1], 1)

    with tf.variable_scope('actor'):
      actor = tfl.makeAffineLayer(self.layer_sizes[-1], action_size)
      smooth = lambda probs: (1.0 - self.epsilon) * probs + self.epsilon / action_size
      actor = util.compose(smooth, tf.nn.softmax, actor)

    self.layers.append(lambda x: (tf.squeeze(values(x)), actor(x)))

  def getLayers(self, state):
    outputs = [state]
    for i, f in enumerate(self.layers):
      with tf.name_scope('layer_%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getOutput(self, state):
    return self.getLayers(state)[-1]

  def getLoss(self, states, actions, rewards):
    n = config.tdN
    train_length = [config.experience_length - n]

    values, actor_probs = self.getOutput(states)
    trainVs = tf.slice(values, [0], train_length)

    # smooth between TD(m) for m<=n?
    targets = tf.slice(values, [n], train_length)
    for i in reversed(range(n)):
      targets = tf.slice(rewards, [i], train_length) + config.discount * targets
    targets = tf.stop_gradient(targets)

    advantages = targets - trainVs
    vLoss = tf.reduce_mean(tf.square(advantages))

    log_actor_probs = tf.log(actor_probs)
    actor_entropy = tf.reduce_mean(tfl.batch_dot(actor_probs, log_actor_probs))
    real_log_actor_probs = tfl.batch_dot(actions, tf.log(actor_probs))
    train_log_actor_probs = tf.slice(real_log_actor_probs, [0], train_length)
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))

    acLoss = vLoss - actor_gain# + actor_entropy

    return acLoss, [('vLoss', vLoss), ('actor_gain', actor_gain), ('actor_entropy', actor_entropy)]

  def getPolicy(self, state):
    return tf.squeeze(self.getOutput(state)[-1])

  def act(self, policy):
    return random.choice(range(self.action_size), p=policy)
