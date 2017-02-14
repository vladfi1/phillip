import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *

class RecurrentActorCritic(Default):
  _options = [
    Option('actor_layers', type=int, nargs='+', default=[128, 128]),
    Option('critic_layers', type=int, nargs='+', default=[128, 128]),

    Option('epsilon', type=float, default=0.02),

    Option('entropy_power', type=float, default=1),
    Option('entropy_scale', type=float, default=0.001),
  ]

  _members = [
    ('optimizer', opt.Optimizer)
  ]

  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.action_size = action_size

    for name in ['actor', 'critic']:
      with tf.variable_scope(name):
        cells = []
        prev_size = state_size
        for i, next_size in enumerate(getattr(self, name + "_layers")):
          with tf.variable_scope("layer_%d" % i):
            cells.append(tfl.GRUCell(prev_size, next_size))
          prev_size = next_size
        rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
      setattr(self, name + "_rnn", rnn)
    
    self.rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
    self.hidden_size = (self.actor_rnn.state_size, self.critic_rnn.state_size)

    with tf.variable_scope('actor/out'):
      self.actor_out = tfl.makeAffineLayer(prev_size, action_size, tf.nn.log_softmax)

    with tf.variable_scope('critic/out'):
      v_out = tfl.makeAffineLayer(prev_size, 1)
      v_out = util.compose(lambda x: tf.squeeze(x, [-1]), v_out)
      self.critic_out = v_out

    self.rlConfig = rlConfig

  def train(self, states, actions, rewards, initial, **unused):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    batch_size = state_shape[0]
    experience_length = state_shape[1]
    
    train_length = experience_length - n
    
    (actor_initial, critic_initial) = initial
    states = tf.unpack(states, axis=1)
    
    actor_outputs, actor_hidden = tfl.rnn(self.actor_rnn, states, actor_initial)
    critic_outputs, critic_hidden = tfl.rnn(self.critic_rnn, states, critic_initial)
    print("Unrolled rnns")
    
    actor_outputs = tf.pack(actor_outputs, 1)
    critic_outputs = tf.pack(critic_outputs, 1)

    values = self.critic_out(critic_outputs)
    log_actor_probs = self.actor_out(actor_outputs)
    actor_probs = tf.exp(log_actor_probs)
    
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
    tf.scalar_summary('advantage', tf.reduce_mean(advantages))
    
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.scalar_summary('v_loss', vLoss)
    
    tf.scalar_summary("v_ev", 1. - vLoss / tfl.sample_variance(targets))

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.scalar_summary('entropy_avg', entropy_avg)
    tf.scalar_summary('entropy_min', tf.reduce_min(entropy))
    
    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = tf.slice(real_log_actor_probs, [0, 0], [-1, train_length])
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))
    actor_loss = - (actor_gain + self.entropy_scale * entropy_avg)
    
    actor_params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
      
    def metric(p1, p2):
      return tf.reduce_mean(tfl.kl(p1, p2))
    
    print("Actor optimizer.")
    train_actor = self.optimizer.optimize(actor_loss, actor_params, log_actor_probs, metric)
    print("Critic optimizer.")
    train_critic = tf.train.AdamOptimizer(1e-4).minimize(vLoss) # TODO: parameterize
    
    return tf.group(train_actor, train_critic)

  def getPolicy(self, state, hidden, **unused):
    state = tf.expand_dims(state, 0)
    hidden = util.deepMap(lambda x: tf.expand_dims(x, 0), hidden)
    
    (actor_hidden, critic_hidden) = hidden
    actor_output, actor_hidden = self.actor_rnn(state, actor_hidden)
    _, critic_hidden = self.critic_rnn(state, critic_hidden)
    
    hidden = (actor_hidden, critic_hidden)
    hidden = util.deepMap(lambda x: tf.squeeze(x, [0]), hidden)
    log_actor_probs = tf.squeeze(self.actor_out(actor_output), [0])
    return tf.exp(log_actor_probs), hidden

  def act(self, policy, verbose=False):
    actor_probs, hidden = policy
    return random.choice(range(self.action_size), p=actor_probs), hidden

