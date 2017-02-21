import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *

class RecurrentDQN(Default):
  _options = [
    Option('q_layers', type=int, nargs='+', default=[128, 128], help="sizes of the dqn hidden layers"),
    Option('epsilon', type=float, default=0.02, help="pick random action with probability EPSILON"),
    Option('temperature', type=float, default=0.01, help="Boltzmann distribution over actions"),
    Option('sarsa', type=bool, default=True, help="use action taken instead of max when computing target Q-values"),
  ]
  
  _members = [
    ('optimizer', opt.Optimizer)
  ]

  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.action_size = action_size
    
    with tf.variable_scope('q'):
      cells = []
      
      prev_size = state_size
      for i, next_size in enumerate(self.q_layers):
        with tf.variable_scope("layer_%d" % i):
          #TODO: choose nl here?
          cells.append(tfl.GRUCell(prev_size, next_size))
        prev_size = next_size
      
      with tf.variable_scope('out'):
        self.q_out = tfl.FCLayer(prev_size, action_size)
        #cells.append(tfl.GRUCell(prev_size, action_size)

      self.q_rnn = tf.nn.rnn_cell.MultiRNNCell(cells)
    
    self.hidden_size = self.q_rnn.state_size
    
    self.rlConfig = rlConfig
    
    self.global_step = global_step
  
  def train(self, states, actions, rewards, initial, **unused):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    batch_size = state_shape[0]
    experience_length = state_shape[1]

    train_length = experience_length - n
    
    # if not natural
    q_outputs, q_hidden = tf.nn.dynamic_rnn(self.q_rnn, states, initial_state=initial)
    
    predictedQs = self.q_out(q_outputs)
    takenQs = tfl.batch_dot(actions, predictedQs)
    trainQs = tf.slice(takenQs, [0, 0], [-1, train_length])
    
    # smooth between TD(m) for m<=n?
    targets = tf.slice(takenQs, [0, n], [-1, train_length])
    #targets = values[:,n:]
    for i in reversed(range(n)):
      targets *= self.rlConfig.discount
      targets += tf.slice(rewards, [0, i], [-1, train_length])
    targets = tf.stop_gradient(targets)
    
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
    tf.scalar_summary("q_uev", qLoss / tfl.sample_variance(targets))
    
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
    
    params = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='q')
    
    def metric(q1, q2):
      return tf.reduce_mean(tf.squared_difference(q1, q2))

    trainQ = self.optimizer.optimize(qLoss, params, predictedQs, metric)
    return trainQ
    
    """
    update_target = lambda: tf.group(*self.q_target.assign(self.q_net), name="update_target")
    should_update = tf.equal(tf.mod(self.global_step, target_delay), 0)
    periodic_update = tf.case([(should_update, update_target)], default=lambda: tf.no_op())
    
    return (
      qLoss,
      [("qLoss", qLoss), ("periodic_update", periodic_update)],
    )
    """
  
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
    return random.choice(range(self.action_size), p=action_probs), hidden

