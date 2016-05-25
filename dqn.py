import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random
import config

class DQN:
  def __init__(self, state_size, action_size, global_step, rlConfig,
    epsilon=0.04, temperature=0.01, **kwargs):
    self.action_size = action_size
    self.layer_sizes = [state_size, 128, 128, action_size]
    self.layers = []

    for i in range(len(self.layer_sizes)-1):
      prev_size = self.layer_sizes[i]
      next_size = self.layer_sizes[i+1]

      with tf.variable_scope("layer_%d" % i):
        self.layers.append(tfl.makeAffineLayer(prev_size, next_size, tfl.leaky_relu))
    
    self.rlConfig = rlConfig
    
    with tf.name_scope('epsilon'):
      #epsilon = tf.constant(0.02)
      self.epsilon = epsilon + 0.5 * tf.exp(-tf.cast(global_step, tf.float32) / 50000.0)

    with tf.name_scope('temperature'):
      #temperature = 0.05  * (0.5 ** (tf.cast(global_step, tf.float32) / 100000.0) + 0.1)
      self.temperature = temperature

  def getLayers(self, state):
    outputs = [state]
    for i, f in enumerate(self.layers):
      with tf.name_scope('q%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getQValues(self, state):
    return self.getLayers(state)[-1]

  def getLoss(self, states, actions, rewards, sarsa=False, **kwargs):
    n = self.rlConfig.tdN
    train_length = [config.experience_length - n]

    qValues = self.getQValues(states)
    realQs = tfl.batch_dot(actions, qValues)
    maxQs = tf.reduce_max(qValues, 1)

    # smooth between TD(m) for m<=n?
    targets = tf.slice(realQs if sarsa else maxQs, [n], train_length)
    for i in reversed(range(n)):
      targets = tf.slice(rewards, [i], train_length) + self.rlConfig.discount * targets
    targets = tf.stop_gradient(targets)

    trainQs = tf.slice(realQs, [0], train_length)

    qLosses = tf.squared_difference(trainQs, targets)
    qLoss = tf.reduce_mean(qLosses)
    return qLoss, [("qLoss", qLoss)]

  def getPolicy(self, state, **kwargs):
    #return [self.epsilon, tf.argmax(self.getQValues(state), 1)]
    qValues = self.getQValues(state)
    action_probs = tf.nn.softmax(qValues / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    entropy = tf.reduce_sum(tf.log(action_probs) * action_probs, 1)
    return [qValues, action_probs, entropy]
  
  def act(self, policy, verbose=False):
    [qValues], [action_probs], [entropy] = policy
    if verbose:
      print("qValues", qValues)
      print("action_probs", action_probs)
      print("entropy", entropy)
    return random.choice(range(self.action_size), p=action_probs)

