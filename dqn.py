import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random

class DQN:
  def __init__(self, state_size, action_size, global_step, rlConfig,
    epsilon=0.04, temperature=0.01, **kwargs):
    self.action_size = action_size
    self.layer_sizes = [128, 128]
    
    self.q_net = tfl.Sequential()
    
    prev_size = state_size
    for i, size in enumerate(self.layer_sizes):
      with tf.variable_scope("layer_%d" % i):
        self.q_net.append(tfl.FCLayer(prev_size, size, tfl.leaky_relu))
      prev_size = size
    
    with tf.variable_scope("q_out"):
      # no non-linearity on output layer
      self.q_net.append(tfl.FCLayer(prev_size, action_size))
    
    self.rlConfig = rlConfig
    
    with tf.name_scope('epsilon'):
      #epsilon = tf.constant(0.02)
      self.epsilon = epsilon# + 0.5 * tf.exp(-tf.cast(global_step, tf.float32) / 10000.0)

    with tf.name_scope('temperature'):
      #temperature = 0.05  * (0.5 ** (tf.cast(global_step, tf.float32) / 100000.0) + 0.1)
      self.temperature = temperature
    
    self.global_step = global_step
  
  def getVariables(self):
    return self.q_net.getVariables()
  
  def getLoss(self, states, actions, rewards, sarsa=False, target_delay=1000, **kwargs):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    state_rank = tf.shape(state_shape)[0]
    experience_length = tf.gather(state_shape, state_rank-2)

    train_length = experience_length - n

    trainQs = self.q_net(states)
    trainQs = tfl.batch_dot(actions, trainQs)
    trainQs = tf.slice(trainQs, [0, 0], [-1, train_length])
    
    self.q_target = self.q_net.clone()
    
    targetQs = self.q_target(states)
    realQs = tfl.batch_dot(actions, targetQs)
    maxQs = tf.reduce_max(targetQs, -1)
    targetQs = realQs if sarsa else maxQs

    # smooth between TD(m) for m<=n?
    targets = tf.slice(targetQs, [0, n], [-1, train_length])
    for i in reversed(range(n)):
      targets = tf.slice(rewards, [0, i], [-1, train_length]) + self.rlConfig.discount * targets
    # not necessary if we optimize only on q_net variables
    # but this is easier :)
    targets = tf.stop_gradient(targets)

    qLosses = tf.squared_difference(trainQs, targets)
    qLoss = tf.reduce_mean(qLosses)
    
    update_target = lambda: tf.group(*self.q_target.assign(self.q_net), name="update_target")
    should_update = tf.equal(tf.mod(self.global_step, target_delay), 0)
    periodic_update = tf.case([(should_update, update_target)], default=lambda: tf.no_op())
    
    #return qLoss, [("qLoss", qLoss)], (1000, update_target)
    return (
      qLoss,
      [("qLoss", qLoss), ("periodic_update", periodic_update)],
      #tf.initialize_variables(self.q_target.getVariables())
    )
  
  def getPolicy(self, state, **kwargs):
    #return [self.epsilon, tf.argmax(self.getQValues(state), 1)]
    state = tf.expand_dims(state, 0)
    qValues = self.q_net(state)
    action_probs = tf.nn.softmax(qValues / self.temperature)
    
    
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    entropy = -tf.reduce_sum(tf.log(action_probs) * action_probs, -1)
    return [qValues, action_probs, entropy]
  
  def act(self, policy, verbose=False):
    [qValues], [action_probs], [entropy] = policy
    if verbose:
      print("qValues", qValues)
      print("action_probs", action_probs)
      print("entropy", entropy)
    return random.choice(range(self.action_size), p=action_probs)

