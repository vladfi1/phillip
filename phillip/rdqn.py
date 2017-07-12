import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *
from . import rl_common as RL

class RecurrentDQN(Default):
  _options = [
    Option('q_layers', type=int, nargs='+', default=[128, 128], help="sizes of the dqn hidden layers"),
    Option('epsilon', type=float, default=0.02, help="pick random action with probability EPSILON"),
    Option('temperature', type=float, default=0.01, help="Boltzmann distribution over actions"),
    Option('sarsa', type=bool, default=True, help="use action taken instead of max when computing target Q-values"),
  ]
  
  _members = [
    ('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]

  def __init__(self, embedGame, embedAction, global_step, rlConfig, scope='q', **kwargs):
    Default.__init__(self, **kwargs)
    self.rlConfig = rlConfig
    
    self.embedGame = embedGame
    self.embedAction = embedAction
    self.action_size = embedAction.size
    
    history_size = (1+rlConfig.memory) * (embedGame.size+self.action_size)
    
    with tf.variable_scope(scope):
      cells = []
      
      prev_size = history_size
      for i, next_size in enumerate(self.q_layers):
        with tf.variable_scope("layer_%d" % i):
          #TODO: choose nl here?
          cells.append(tfl.GRUCell(prev_size, next_size, self.nl))
        prev_size = next_size
      
      with tf.variable_scope('out'):
        self.q_out = tfl.FCLayer(prev_size, self.action_size)

      self.q_rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
    
    self.hidden_size = self.q_rnn.state_size
    
    self.global_step = global_step
  
  def train(self, state, prev_action, action, initial, targets, **unused):
    embedded_state = self.embedGame(state)
    embedded_prev_action = self.embedAction(prev_action)
    history = RL.makeHistory(embedded_state, embedded_prev_action, self.rlConfig.memory)
    actions = self.embedAction(action[:,self.rlConfig.memory:])
    
    # if not natural
    q_outputs, q_hidden = tf.nn.dynamic_rnn(self.q_rnn, history, initial_state=initial)
    
    predictedQs = self.q_out(q_outputs)
    takenQs = tfl.batch_dot(actions, predictedQs)
    trainQs = takenQs[:,:-1]
    
    qLoss = tf.reduce_mean(tf.squared_difference(trainQs, targets))
    tf.summary.scalar("q_loss", qLoss)
    tf.summary.scalar("q_uev", qLoss / tfl.sample_variance(targets))
    
    # all this just to log entropy statistics
    flatQs = tf.reshape(predictedQs, [-1, self.action_size])
    action_probs = tf.nn.softmax(flatQs / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    log_action_probs = tf.log(action_probs)
    entropy = -tfl.batch_dot(action_probs, log_action_probs)
    tf.summary.scalar("entropy_avg", tf.reduce_mean(entropy))
    tf.summary.histogram("entropy", entropy)
    
    meanQs = tfl.batch_dot(action_probs, flatQs)
    tf.summary.scalar("q_mean", tf.reduce_mean(meanQs))
    
    params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='q')
    
    def metric(q1, q2):
      return tf.reduce_mean(tf.squared_difference(q1, q2))

    trainQ = self.optimizer.optimize(qLoss, params, predictedQs, metric)
    return trainQ
  
  def getPolicy(self, state, hidden, **unused):
    #return [self.epsilon, tf.argmax(self.getQValues(state), 1)]
    state = tf.expand_dims(state, 0)
    hidden = util.deepMap(lambda x: tf.expand_dims(x, 0), hidden)
    
    outputs, hidden = self.q_rnn(state, hidden)
    qValues = self.q_out(outputs)
    
    action_probs = tf.nn.softmax(qValues / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    action_probs = tf.squeeze(action_probs, [0])
    
    hidden = util.deepMap(lambda x: tf.squeeze(x, [0]), hidden)
    
    log_action_probs = tf.log(action_probs)
    entropy = - tfl.dot(action_probs, log_action_probs)

    return action_probs, tf.squeeze(qValues), entropy, hidden
  
  def act(self, policy, verbose=False):
    action_probs, qValues, entropy, hidden = policy
    if verbose:
      #print(qValues)
      print(entropy)
    action = random.choice(range(self.embedAction.size), p=action_probs)
    return action, action_probs[action], hidden
