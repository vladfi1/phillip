import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random
from default import *

class DQN(Default):
  _options = [
    Option('q_layers', type=int, nargs='+', default=[128, 128], help="sizes of the dqn hidden layers"),
    Option('epsilon', type=float, default=0.02, help="pick random action with probability EPSILON"),
    Option('temperature', type=float, default=0.01, help="Boltzmann distribution over actions"),
    Option('sarsa', type=bool, default=True, help="use action taken instead of max when computing target Q-values"),
    Option('learning_rate', type=float, default=0.001),
    #Option('optimizer', type=str, default='Adam'
  ]

  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.action_size = action_size
    
    self.q_net = tfl.Sequential()
    
    prev_size = state_size
    for i, size in enumerate(self.q_layers):
      with tf.variable_scope("layer_%d" % i):
        self.q_net.append(tfl.FCLayer(prev_size, size, tfl.leaky_softplus()))
      prev_size = size
    
    with tf.variable_scope("q_out"):
      # no non-linearity on output layer
      self.q_net.append(tfl.FCLayer(prev_size, action_size))
    
    self.rlConfig = rlConfig
    
    self.global_step = global_step
  
  def getVariables(self):
    return self.q_net.getVariables()
  
  def train(self, states, actions, rewards):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    state_rank = tf.shape(state_shape)[0]
    experience_length = tf.gather(state_shape, state_rank-2)

    train_length = experience_length - n

    self.predictedQs = self.q_net(states)
    trainQs = tfl.batch_dot(actions, self.predictedQs)
    trainQs = tf.slice(trainQs, [0, 0], [-1, train_length])
    
    self.q_target = self.q_net#.clone()
    
    targetQs = self.q_target(states)
    realQs = tfl.batch_dot(actions, targetQs)
    maxQs = tf.reduce_max(targetQs, -1)
    targetQs = realQs if self.sarsa else maxQs
    
    tf.scalar_summary("q_mean", tf.reduce_mean(self.predictedQs))
    tf.scalar_summary("q_max", tf.reduce_mean(maxQs))
    
    # smooth between TD(m) for m<=n?
    targets = tf.slice(targetQs, [0, n], [-1, train_length])
    for i in reversed(range(n)):
      targets = tf.slice(rewards, [0, i], [-1, train_length]) + self.rlConfig.discount * targets
    targets = tf.stop_gradient(targets)

    qLosses = tf.squared_difference(trainQs, targets)
    qLoss = tf.reduce_mean(qLosses)
    tf.scalar_summary("q_loss", qLoss)
    
    variance = tf.reduce_mean(tf.squared_difference(targets, tf.reduce_mean(targets)))
    explained_variance = 1 - qLoss / variance
    tf.scalar_summary("explained_variance", explained_variance)
    
    flatQs = tf.reshape(self.predictedQs, [-1, self.action_size])
    action_probs = tf.nn.softmax(flatQs / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    entropy = -tf.reduce_sum(tf.log(action_probs) * action_probs, -1)
    entropy = tf.reduce_mean(entropy)
    tf.scalar_summary("entropy", entropy)
    
    self.params = tf.trainable_variables()
    self.gradients = tf.gradients(qLoss, self.params, -self.learning_rate)
    
    return tfl.apply_grads(self.params, self.gradients)
    
    """
    update_target = lambda: tf.group(*self.q_target.assign(self.q_net), name="update_target")
    should_update = tf.equal(tf.mod(self.global_step, target_delay), 0)
    periodic_update = tf.case([(should_update, update_target)], default=lambda: tf.no_op())
    
    return (
      qLoss,
      [("qLoss", qLoss), ("periodic_update", periodic_update)],
    )
    """
  
  def getPolicy(self, state):
    #return [self.epsilon, tf.argmax(self.getQValues(state), 1)]
    state = tf.expand_dims(state, 0)
    qValues = self.q_net(state)
    
    if self.temperature:
      action = tf.multinomial(qValues / self.temperature, 1)
    else:
      action = tf.argmax(qValues, 1)
    
    if self.epsilon:
      greedy = tf.random_uniform([]) > self.epsilon
      random_action = lambda: tf.multinomial(tf.constant(0., shape=[1, self.action_size]), 1)
      action = tf.cond(greedy, lambda: action, random_action)
    
    action = tf.squeeze(action)

    return action, tf.squeeze(qValues)
  
  def act(self, policy, verbose=False):
    action, qValues = policy
    if verbose:
      print(qValues)
    return action
