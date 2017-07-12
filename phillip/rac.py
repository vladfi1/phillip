import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *
from . import rl_common as RL

class RecurrentActorCritic(Default):
  _options = [
    Option('actor_layers', type=int, nargs='+', default=[128, 128]),

    Option('epsilon', type=float, default=0.02),

    Option('entropy_power', type=float, default=1),
    Option('entropy_scale', type=float, default=0.001),
    
    Option('dynamic', type=int, default=1, help='dynamically unroll rnn'),
    Option('initial', type=str, default='zero', choices=['zero', 'train', 'agent'])
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

    with tf.variable_scope(name):
      cells = []
      prev_size = history_size
      for i, next_size in enumerate(getattr(self, name + "_layers")):
        with tf.variable_scope("layer_%d" % i):
          cells.append(tfl.GRUCell(prev_size, next_size))
        prev_size = next_size
      self.rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
      
      with tf.variable_scope("out"):
        self.actor_out = tfl.makeAffineLayer(prev_size, action_size, tf.nn.log_softmax)

    if self.initial == 'agent':
      self.hidden_size = self.rnn.state_size
    else:
      self.hidden_size = tuple()

      self.initial_state = tuple(tf.Variable(tf.zeros(shape),
                                             trainable=self.initial=='train',
                                             name='hidden_%d'%i)
                                 for i, shape in enumerate(self.rnn.state_size))

  def train(self, state, prev_action, action, advantages, initial, **unused):
    embedded_state = self.embedGame(state)
    embedded_prev_action = self.embedAction(prev_action)
    history = RL.makeHistory(embedded_state, embedded_prev_action, self.rlConfig.memory)

    if self.initial != 'agent':
      batch_size = tf.shape(history)[:1]

      def expand(t):
        ones = tf.ones_like(tf.shape(t), tf.int32)
        multiples = tf.concat(axis=0, values=[batch_size, ones])
        return tf.tile(tf.expand_dims(t, 0), multiples)

      initial = util.deepMap(expand, self.initial_state)
    
    if self.dynamic:
      actor_outputs, actor_hidden = tf.nn.dynamic_rnn(self.rnn, history, initial_state=initial)
    else:
      actor_outputs, actor_hidden = tfl.rnn(self.rnn, history, initial)
    log_actor_probs = self.actor_out(actor_outputs)
    actor_probs = tf.exp(log_actor_probs)

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.summary.scalar('entropy_avg', entropy_avg)
    tf.summary.scalar('entropy_min', tf.reduce_min(entropy))
    tf.summary.histogram('entropy', entropy)

    actions = self.embedAction(action[:,self.rlConfig.memory:])
    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = real_log_actor_probs[:,:-1] # last state has no advantage
    actor_gain = tf.reduce_mean(tf.multiply(train_log_actor_probs, tf.stop_gradient(advantages)))
    #tf.scalar_summary('actor_gain', actor_gain)
    
    actor_loss = - (actor_gain + self.entropy_scale * entropy_avg)
    
    actor_params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
      
    def metric(p1, p2):
      return tf.reduce_mean(tfl.kl(p1, p2))
    
    print("Actor optimizer.")
    return self.optimizer.optimize(actor_loss, actor_params, log_actor_probs, metric)

  def getPolicy(self, state, hidden, **unused):
    state = tf.expand_dims(state, 0)

    if self.initial != 'agent':
      hidden = self.initial_state
    
    hidden = util.deepMap(lambda x: tf.expand_dims(x, 0), hidden)
    
    actor_output, actor_hidden = self.rnn(state, hidden)
    
    hidden = util.deepMap(lambda x: tf.squeeze(x, [0]), hidden)

    if self.initial != 'agent':
      hidden = util.deepZipWith(tf.assign, self.initial_state, hidden)
    
    log_actor_probs = tf.squeeze(self.actor_out(actor_output), [0])
    return tf.exp(log_actor_probs), hidden

  def act(self, policy, verbose=False):
    actor_probs, hidden = policy
    action = random.choice(range(self.embedAction.size), p=actor_probs)
    return action, actor_probs[action], hidden

