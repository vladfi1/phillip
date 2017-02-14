import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *

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

  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.action_size = action_size
    
    # TODO: share q and v networks?
    for name in ['q', 'v']:
      net = tfl.Sequential()
      
      prev_size = state_size
      for i, size in enumerate(self.q_layers):
        with tf.variable_scope("layer_%d" % i):
          net.append(tfl.FCLayer(prev_size, size, self.nl))
        prev_size = size
      
      setattr(self, name + '_net', net)
    
    with tf.variable_scope("q_out"):
      # no non-linearity on output layer
      self.q_net.append(tfl.FCLayer(prev_size, action_size))

    with tf.variable_scope("v_out"):
      # no non-linearity on output layer
      self.v_net.append(tfl.FCLayer(prev_size, 1))
    
    self.rlConfig = rlConfig
    
    self.global_step = global_step
  
  def getVariables(self):
    return self.q_net.getVariables()
  
  def train(self, states, actions, rewards, **unused):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    state_rank = tf.shape(state_shape)[0]
    experience_length = tf.gather(state_shape, state_rank-2)

    train_length = experience_length - n

    predictedVs = tf.squeeze(self.v_net(states), [-1])
    trainVs = tf.slice(predictedVs, [0, 0], [-1, train_length])

    predictedQs = self.q_net(states)
    takenQs = tfl.batch_dot(actions, predictedQs)
    trainQs = tf.slice(takenQs, [0, 0], [-1, train_length])
    
    # smooth between TD(m) for m<=n?
    targets = tf.slice(predictedVs, [0, n], [-1, train_length])
    #targets = tf.slice(takenQs, [0, n], [-1, train_length])
    #targets = values[:,n:]
    for i in reversed(range(n)):
      targets *= self.rlConfig.discount
      targets += tf.slice(rewards, [0, i], [-1, train_length])
    targets = tf.stop_gradient(targets)

    advantages = targets - trainVs
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.scalar_summary('v_loss', vLoss)
    tf.scalar_summary("v_uev", vLoss / tfl.sample_variance(targets))
    
    #self.q_target = self.q_net#.clone()
    #targetQs = self.q_target(states)
    
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
    tf.scalar_summary("q_loss", qLoss)
    tf.scalar_summary("q_uev", qLoss / vLoss)
    
    # all this just to log entropy statistics
    flatQs = tf.reshape(predictedQs, [-1, self.action_size])
    action_probs = tf.nn.softmax(flatQs / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    log_action_probs = tf.log(action_probs)
    entropy = -tfl.batch_dot(action_probs, log_action_probs)
    tf.scalar_summary("entropy_avg", tf.reduce_mean(entropy))
    tf.histogram_summary("entropy", entropy)
    
    meanQs = tfl.batch_dot(action_probs, flatQs)
    tf.scalar_summary("q_mean", tf.reduce_mean(meanQs))
    
    params = self.q_net.getVariables()
    
    def metric(q1, q2):
      return tf.reduce_mean(tf.squared_difference(q1, q2))

    trainQ = self.optimizer.optimize(qLoss, params, predictedQs, metric)
    trainV = tf.train.AdamOptimizer(1e-4).minimize(vLoss) # TODO: parameterize
    
    return tf.group(trainQ, trainV)
    
    """
    update_target = lambda: tf.group(*self.q_target.assign(self.q_net), name="update_target")
    should_update = tf.equal(tf.mod(self.global_step, target_delay), 0)
    periodic_update = tf.case([(should_update, update_target)], default=lambda: tf.no_op())
    
    return (
      qLoss,
      [("qLoss", qLoss), ("periodic_update", periodic_update)],
    )
    """
  
  def getPolicy(self, state, **unused):
    #return [self.epsilon, tf.argmax(self.getQValues(state), 1)]
    state = tf.expand_dims(state, 0)
    qValues = self.q_net(state)
    
    action_probs = tf.nn.softmax(qValues / self.temperature)
    action_probs = (1.0 - self.epsilon) * action_probs + self.epsilon / self.action_size
    action_probs = tf.squeeze(action_probs)
    
    log_action_probs = tf.log(action_probs)
    entropy = - tfl.dot(action_probs, log_action_probs)

    return action_probs, tf.squeeze(qValues), entropy
  
  def act(self, policy, verbose=False):
    action_probs, qValues, entropy = policy
    if verbose:
      #print(qValues)
      print(entropy)
    return random.choice(range(self.action_size), p=action_probs), []

