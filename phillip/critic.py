import tensorflow as tf
from . import tf_lib as tfl
from .default import *
from .RL import RLConfig
#from .embed import GameEmbedding

class Critic(Default):
  _options = [
    Option('critic_layers', type=int, nargs='+', default=[128, 128]),
    Option('critic_learning_rate', type=float, default=1e-4),
    Option('gae_lamdba', type=float, default=1., help="Generalized Advantage Estimation"),
    Option('fix_scopes', type=bool, default=False),
  ]
  
  _members = [
    ('rlConfig', RLConfig),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, state_size, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.net = tfl.Sequential()
    with tf.variable_scope("critic"):
      prev_size = state_size
      for i, next_size in enumerate(self.critic_layers):
        with tf.variable_scope("layer_%d" % i):
          self.net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      
      if self.fix_scopes:
        self.net.append(tfl.FCLayer(prev_size, 1))
      
    if not self.fix_scopes:
      with tf.variable_scope('critic'):
        self.net.append(tfl.FCLayer(prev_size, 1))
  
  def __call__(self, states, rewards):
    values = tf.squeeze(self.net(states), [-1])
    trainVs = values[:,:-1]
    lastV = values[:,-1]
    
    # TODO: implement GAE, or some TD(N) weighting scheme
    targets = tfl.discount(rewards, self.rlConfig.discount, lastV)
    targets = tf.stop_gradient(targets)
    
    advantages = targets - trainVs
    advantage_avg = tf.reduce_mean(advantages)
    tf.scalar_summary('advantage_avg', advantage_avg)
    tf.scalar_summary('advantage_std', tf.sqrt(tf.reduce_mean(tf.squared_difference(advantages, advantage_avg))))
    
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.scalar_summary('v_loss', vLoss)
    tf.scalar_summary("v_uev", vLoss / tfl.sample_variance(targets))
    
    train_critic = tf.train.AdamOptimizer(self.critic_learning_rate).minimize(vLoss)
    
    return train_critic, targets, advantages

