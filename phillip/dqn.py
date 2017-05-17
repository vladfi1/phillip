import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *
from . import rl_common as RL

class DQN(Default):
  hidden_size = []
  
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
    action_size = embedAction.size
    
    history_size = (1+rlConfig.memory) * (embedGame.size+action_size)

    with tf.variable_scope(scope):
      self.net = tfl.Sequential()
      prev_size = history_size
      for i, size in enumerate(self.q_layers):
        with tf.variable_scope("layer_%d" % i):
          self.net.append(tfl.FCLayer(prev_size, size, self.nl))
        prev_size = size

      with tf.variable_scope("out"):
        # no non-linearity on output layer
        self.net.append(tfl.FCLayer(prev_size, action_size))
    
    self.global_step = global_step
  
  def getVariables(self):
    return self.net.getVariables()
  
  def train(self, state, prev_action, action, targets, **unused):
    embedded_state = self.embedGame(state)
    embedded_prev_action = self.embedAction(prev_action)
    history = RL.makeHistory(embedded_state, embedded_prev_action, self.rlConfig.memory)
    actions = self.embedAction(action[:,self.rlConfig.memory:])
    
    predictedQs = self.net(history)
    takenQs = tfl.batch_dot(actions, predictedQs)
    trainQs = takenQs[:,:-1]
    
    """ TODO: do we still want this code path for maxQ/sarsa?
    targetQs = predictedQs
    realQs = tfl.batch_dot(actions, targetQs)
    maxQs = tf.reduce_max(targetQs, -1)
    targetQs = realQs if self.sarsa else maxQs
    
    tf.scalar_summary("q_max", tf.reduce_mean(maxQs))
    
    # smooth between TD(m) for m<=n?
    targets = tf.slice(targetQs, [0, n], [-1, train_length])
    for i in reversed(range(n)):
      targets = tf.slice(rewards, [0, i], [-1, train_length]) + self.rlConfig.discount * targets
    targets = tf.stop_gradient(targets)
    """
    
    qLoss = tf.reduce_mean(tf.squared_difference(trainQs, targets))
    tf.summary.scalar("q_loss", qLoss)
    tf.summary.scalar("q_uev", qLoss / tfl.sample_variance(targets))
    
    # all this just to log entropy statistics
    flatQs = tf.reshape(predictedQs, [-1, self.embedAction.size])
    action_probs = tf.nn.softmax(flatQs / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.embedAction.size
    log_action_probs = tf.log(action_probs)
    entropy = -tfl.batch_dot(action_probs, log_action_probs)
    tf.summary.scalar("entropy_avg", tf.reduce_mean(entropy))
    tf.summary.histogram("entropy", entropy)
    
    meanQs = tfl.batch_dot(action_probs, flatQs)
    tf.summary.scalar("q_mean", tf.reduce_mean(meanQs))
    # tf.histogram_summary("q", )

    params = self.net.getVariables()
    
    def metric(q1, q2):
      return tf.reduce_mean(tf.squared_difference(q1, q2))

    return self.optimizer.optimize(qLoss, params, predictedQs, metric)
  
  def getPolicy(self, state, **unused):
    #return [self.epsilon, tf.argmax(self.getQValues(state), 1)]
    state = tf.expand_dims(state, 0)
    qValues = self.net(state)
    
    action_probs = tf.nn.softmax(qValues / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.embedAction.size
    action_probs = tf.squeeze(action_probs)
    
    log_action_probs = tf.log(action_probs)
    entropy = - tfl.dot(action_probs, log_action_probs)

    return action_probs, tf.squeeze(qValues), entropy
  
  def act(self, policy, verbose=False):
    action_probs, qValues, entropy = policy
    if verbose:
      #print(qValues)
      print(entropy)
    action = random.choice(range(self.embedAction.size), p=action_probs)
    return action, action_probs[action], []

