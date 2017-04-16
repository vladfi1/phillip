import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *
from . import rl_common as RL

class RecurrentActorCritic(Default):
  _options = [
    Option('actor_fc_layers', type=int, nargs='+', default=[128]),
    Option('actor_rnn_layers', type=int, nargs='+', default=[128]),

    Option('epsilon', type=float, default=0.02),

    Option('entropy_power', type=float, default=1),
    Option('entropy_scale', type=float, default=0.001),
    
    Option('dynamic', type=int, default=1, help='dynamically unroll rnn'),
  ]

  _members = [
    ('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]

  def __init__(self, embedGame, embedAction, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.rlConfig = rlConfig
    
    self.embedGame = embedGame
    self.embedAction = embedAction
    action_size = embedAction.size
    
    history_size = (1+rlConfig.memory) * (embedGame.size+embedAction.size)
    
    name = 'actor'

    net = tfl.Sequential()
    with tf.variable_scope(name):
      prev_size = history_size
      for i, next_size in enumerate(getattr(self, name + "_fc_layers")):
        with tf.variable_scope("fc_layer_%d" % i):
          net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      self.actor_fc = net

      cells = []
      for i, next_size in enumerate(getattr(self, name + "_rnn_layers")):
        with tf.variable_scope("rnn_layer_%d" % i):
          cells.append(tfl.GRUCell(prev_size, next_size))
        prev_size = next_size
      self.rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
      
      with tf.variable_scope("out"):
        self.actor_out = tfl.makeAffineLayer(prev_size, action_size, tf.nn.log_softmax)
    
    self.hidden_size = self.rnn.state_size

  def train(self, state, prev_action, action, advantages, initial, **unused):
    embedded_state = self.embedGame(state)
    embedded_prev_action = self.embedAction(prev_action)
    history = RL.makeHistory(embedded_state, embedded_prev_action, self.rlConfig.memory)
    
    history = self.actor_fc(history)
    if self.dynamic:
      actor_outputs, actor_hidden = tf.nn.dynamic_rnn(self.rnn, history, initial_state=initial)
    else:
      actor_outputs, actor_hidden = tfl.rnn(self.rnn, history, initial)
    log_actor_probs = self.actor_out(actor_outputs)
    actor_probs = tf.exp(log_actor_probs)

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.scalar_summary('entropy_avg', entropy_avg)
    tf.scalar_summary('entropy_min', tf.reduce_min(entropy))
    tf.histogram_summary('entropy', entropy)

    actions = self.embedAction(action[:,self.rlConfig.memory:])
    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = real_log_actor_probs[:,:-1] # last state has no advantage
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))
    #tf.scalar_summary('actor_gain', actor_gain)
    
    actor_loss = - (actor_gain + self.entropy_scale * entropy_avg)
    
    actor_params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
      
    def metric(p1, p2):
      return tf.reduce_mean(tfl.kl(p1, p2))
    
    print("Actor optimizer.")
    return self.optimizer.optimize(actor_loss, actor_params, log_actor_probs, metric)

  def getPolicy(self, state, hidden, **unused):
    state = tf.expand_dims(state, 0)
    hidden = util.deepMap(lambda x: tf.expand_dims(x, 0), hidden)
    
    actor_output, actor_hidden = self.rnn(state, hidden)
    
    hidden = util.deepMap(lambda x: tf.squeeze(x, [0]), hidden)
    log_actor_probs = tf.squeeze(self.actor_out(actor_output), [0])
    return tf.exp(log_actor_probs), hidden

  def act(self, policy, verbose=False):
    actor_probs, hidden = policy
    action = random.choice(range(self.embedAction.size), p=actor_probs)
    return action, actor_probs[action], hidden

