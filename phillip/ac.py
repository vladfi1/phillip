import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *

class ActorCritic(Default):
  hidden_size = []
  
  _options = [
    Option('actor_layers', type=int, nargs='+', default=[128, 128]),
    Option('critic_layers', type=int, nargs='+', default=[128, 128]),
    Option('fix_scopes', type=bool, default=False),

    Option('epsilon', type=float, default=0.02),

    Option('entropy_power', type=float, default=1),
    Option('entropy_scale', type=float, default=0.001),
  ]

  _members = [
    ('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.action_size = action_size

    for name in ['actor', 'critic']:
      net = tfl.Sequential()
      with tf.variable_scope(name):
        prev_size = state_size
        for i, next_size in enumerate(getattr(self, name + "_layers")):
          with tf.variable_scope("layer_%d" % i):
            net.append(tfl.FCLayer(prev_size, next_size, self.nl))
          prev_size = next_size
        
        if self.fix_scopes:
          if name == 'actor':
            net.append(tfl.FCLayer(prev_size, action_size, lambda p: (1. - self.epsilon) * tf.nn.softmax(p) + self.epsilon / action_size))
          else:
            net.append(tfl.FCLayer(prev_size, 1))
      
      setattr(self, name, net)
      
    if not self.fix_scopes:
      with tf.variable_scope('actor'):
        self.actor.append(tfl.FCLayer(prev_size, action_size, lambda p: (1. - self.epsilon) * tf.nn.softmax(p) + self.epsilon / action_size))

      with tf.variable_scope('critic'):
        self.critic.append(tfl.FCLayer(prev_size, 1))

    self.rlConfig = rlConfig

  def train(self, states, actions, rewards, **unused):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    state_rank = tf.shape(state_shape)[0]
    experience_length = tf.gather(state_shape, state_rank-2)
    
    train_length = experience_length - n

    values = tf.squeeze(self.critic(states), [-1])
    actor_probs = self.actor(states)
    log_actor_probs = tf.log(actor_probs)
    
    trainVs = tf.slice(values, [0, 0], [-1, train_length])
    #trainVs = values[:,:train_length]

    # smooth between TD(m) for m<=n?
    targets = tf.slice(values, [0, n], [-1, train_length])
    #targets = values[:,n:]
    for i in reversed(range(n)):
      targets *= self.rlConfig.discount
      targets += tf.slice(rewards, [0, i], [-1, train_length])
    targets = tf.stop_gradient(targets)

    advantages = targets - trainVs
    advantage_avg = tf.reduce_mean(advantages)
    tf.scalar_summary('advantage_avg', advantage_avg)
    tf.scalar_summary('advantage_std', tf.sqrt(tf.reduce_mean(tf.squared_difference(advantages, advantage_avg))))
    
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.scalar_summary('v_loss', vLoss)
    tf.scalar_summary("v_uev", vLoss / tfl.sample_variance(targets))

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.scalar_summary('entropy_avg', entropy_avg)
    tf.scalar_summary('entropy_min', tf.reduce_min(entropy))
    tf.histogram_summary('entropy', entropy)

    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = tf.slice(real_log_actor_probs, [0, 0], [-1, train_length])
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))
    #tf.scalar_summary('actor_gain', actor_gain)
    
    actor_loss = - (actor_gain + self.entropy_scale * entropy_avg)
    
    actor_params = self.actor.getVariables()
      
    def metric(p1, p2):
      return tf.reduce_mean(tfl.kl(p1, p2))
    
    train_actor = self.optimizer.optimize(actor_loss, actor_params, log_actor_probs, metric)
    train_critic = tf.train.AdamOptimizer(1e-4).minimize(vLoss) # TODO: parameterize
    
    return tf.group(train_actor, train_critic)
  
  def getPolicy(self, state, **unused):
    return self.actor(state)

  def act(self, policy, verbose=False):
    return random.choice(range(self.action_size), p=policy), []

