import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random, exp, argmax

class ThompsonDQN:
  def __init__(self, state_size, action_size, global_step, rlConfig, epsilon=0.04, **kwargs):
    self.action_size = action_size
    self.layer_sizes = [state_size, 128, 128]
    self.layers = []

    for i in range(len(self.layer_sizes)-1):
      prev_size = self.layer_sizes[i]
      next_size = self.layer_sizes[i+1]

      with tf.variable_scope("layer_%d" % i):
        self.layers.append(tfl.makeAffineLayer(prev_size, next_size, tfl.leaky_relu))

    with tf.variable_scope('mean'):
      mean = tfl.makeAffineLayer(self.layer_sizes[-1], action_size)

    with tf.variable_scope('log_variance'):
      log_variance = tfl.makeAffineLayer(self.layer_sizes[-1], action_size)

    self.layers.append(lambda x: (mean(x), log_variance(x)))
    
    self.rlConfig = rlConfig
    self.epsilon = epsilon

  def getLayers(self, state):
    outputs = [state]
    for i, f in enumerate(self.layers):
      with tf.name_scope('q%d' % i):
        outputs.append(f(outputs[-1]))

    return outputs

  def getQDists(self, state):
    return self.getLayers(state)[-1]

  def getQValues(self, state):
    return self.getQDists(state)[0]

  def getLoss(self, states, actions, rewards, sarsa=False, **kwargs):
    "Negative Log-Likelihood"
    
    n = self.rlConfig.tdN
    train_length = [config.experience_length - n]
    
    qMeans, qLogVariances = self.getQDists(states)
    
    realQs = tfl.batch_dot(actions, qMeans)
    maxQs = tf.reduce_max(qMeans, 1)

    # smooth between TD(m) for m<=n?
    targets = tf.slice(realQs if sarsa else maxQs, [n], train_length)
    for i in reversed(range(n)):
      targets = tf.slice(rewards, [i], train_length) + self.rlConfig.discount * targets
    targets = tf.stop_gradient(targets)

    trainQs = tf.slice(realQs, [0], train_length)
    
    realLogVariances =  tfl.batch_dot(actions, qLogVariances)
    trainLogVariances = tf.slice(realLogVariances, [0], train_length)
    
    nlls = tf.squared_difference(trainQs, targets) * tf.exp(-trainLogVariances) + trainLogVariances
    nll = tf.reduce_mean(nlls)
    return nll, [("nll", nll)]

  def getPolicy(self, state, policy=None, temperature=1, **kwargs):
    qMeans, qLogVariances = self.getQDists(state)
    qSTDs = tf.exp(qLogVariances / 2) * temperature
    qDists = tf.concat(2, [tf.expand_dims(x, 2) for x in [qMeans, qSTDs]])
    return qDists
  
  def act(self, policy, verbose=False):
    if util.flip(self.epsilon):
      return random.randint(0, self.action_size)
    
    [qDists] = policy
    if verbose:
      print("qDists", qDists)
    
    samples = [random.normal(mean, std) for mean, std in qDists]
    return argmax(samples)

