import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random

class RAC:
  def __init__(self, state_size, action_size, global_step, rlConfig, epsilon=0.02, **kwargs):
    self.action_size = action_size
    self.layer_sizes = [128, 128]
    self.layers = []

    with tf.name_scope('epsilon'):
      #epsilon = tf.constant(0.02)
      self.epsilon = epsilon# + 0.5 * tf.exp(-tf.cast(global_step, tf.float32) / 50000.0)
    
    prev_size = state_size
    cells = []
    for size in self.layer_sizes:
      cells.append(tfl.GRUCell(prev_size, size))
      prev_size = size
    
    self.rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
    self.initial_state = tfl.bias_variable([self.rnn.state_size])

    with tf.variable_scope('actor'):
      actor = tfl.makeAffineLayer(prev_size, action_size, tf.nn.softmax)
      smooth = lambda probs: (1.0 - self.epsilon) * probs + self.epsilon / action_size
      actor = util.compose(smooth, actor)
      self.actor = actor

    with tf.variable_scope('critic'):
      v_out = tfl.makeAffineLayer(prev_size, 1)
      v_out = util.compose(lambda x: tf.squeeze(x, [-1]), v_out)
      self.critic = v_out

    self.rlConfig = rlConfig

  def getLoss(self, states, actions, rewards, entropy_scale=0.001, policy_scale=0.01, **kwargs):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    batch_size = state_shape[0]
    experience_length = state_shape[1]
    
    train_length = experience_length - n
    
    initial_state = tf.expand_dims(self.initial_state, 0)
    initial_state = tf.tile(initial_state, tf.pack([batch_size, 1]))
    outputs, hidden = tf.nn.dynamic_rnn(self.rnn, states, initial_state=initial_state)

    values = self.critic(outputs)
    actor_probs = self.actor(outputs)
    
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
    real_log_actor_probs = tfl.batch_dot(actions, tf.log(actor_probs))
    train_log_actor_probs = tf.slice(real_log_actor_probs, [0, 0], [-1, train_length])
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))

    acLoss = vLoss - policy_scale * (actor_gain + entropy_scale * actor_entropy)

    return acLoss, [('vLoss', vLoss), ('actor_gain', actor_gain), ('actor_entropy', actor_entropy)]

  def getPolicy(self, state, **kwargs):
    state = tf.expand_dims(state, 0)
    initial_state = tf.expand_dims(self.initial_state, 0)
    output, hidden = self.rnn(state, initial_state)
    output = tf.squeeze(output, [0])
    hidden = tf.squeeze(hidden, [0])
    return self.actor(output), tf.assign(self.initial_state, hidden)

  def act(self, policy, verbose=False):
    return random.choice(range(self.action_size), p=policy[0])
