import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random

class ActorCritic:
  def __init__(self, state_size, action_size, global_step, rlConfig, epsilon=0.04, **kwargs):
    self.action_size = action_size
    self.layer_sizes = [128, 128]
    self.layers = []

    with tf.name_scope('epsilon'):
      #epsilon = tf.constant(0.02)
      self.epsilon = epsilon# + 0.5 * tf.exp(-tf.cast(global_step, tf.float32) / 50000.0)

    prev_size = state_size
    for i, next_size in enumerate(self.layer_sizes):
      with tf.variable_scope("layer_%d" % i):
        self.layers.append(tfl.makeAffineLayer(prev_size, next_size, tfl.leaky_relu))
      prev_size = next_size

    with tf.variable_scope('value'):
      v_out = tfl.makeAffineLayer(prev_size, 1)
      v_out = util.compose(lambda x: tf.squeeze(x, [-1]), v_out)

    with tf.variable_scope('actor'):
      actor = tfl.makeAffineLayer(prev_size, action_size, tf.nn.softmax)
      smooth = lambda probs: (1.0 - self.epsilon) * probs + self.epsilon / action_size
      actor = util.compose(smooth, actor)

    self.layers.append(lambda x: (v_out(x), actor(x)))

    self.rlConfig = rlConfig

  def getLayers(self, state):
    outputs = [state]
    for i, f in enumerate(self.layers):
      with tf.name_scope('layer_%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getOutput(self, state):
    return self.getLayers(state)[-1]

  def getLoss(self, states, actions, rewards, entropy_scale=0.01, policy_scale=1.0, **kwargs):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    state_rank = tf.shape(state_shape)[0]
    experience_length = tf.gather(state_shape, state_rank-2)
    
    train_length = experience_length - n

    values, actor_probs = self.getOutput(states)
    trainVs = tf.slice(values, [0, 0], [-1, train_length])
    #trainVs = values[:,:train_length]

    # smooth between TD(m) for m<=n?
    targets = tf.slice(values, [0, n], [-1, train_length])
    #targets = values[:,n:]
    for i in reversed(range(n)):
      targets *= self.rlConfig.discount
      targets += tf.slice(rewards, [0, i], [-1, train_length])
    targets = tf.stop_gradient(targets)

    advantages = targets - trainVs
    vLoss = tf.reduce_mean(tf.square(advantages))

    log_actor_probs = tf.log(actor_probs)
    actor_entropy = -tf.reduce_mean(tfl.batch_dot(actor_probs, log_actor_probs))
    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = tf.slice(real_log_actor_probs, [0, 0], [-1, train_length])
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))

    acLoss = vLoss - policy_scale * (actor_gain + entropy_scale * actor_entropy)

    return acLoss, [('vLoss', vLoss), ('actor_gain', actor_gain), ('actor_entropy', actor_entropy)]

  def getPolicy(self, state, **kwargs):
    return self.getOutput(state)[1]

  def act(self, policy, verbose=False):
    return random.choice(range(self.action_size), p=policy)
