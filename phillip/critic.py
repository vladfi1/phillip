import tensorflow as tf
from . import tf_lib as tfl
from .default import *
from .rl_common import *
#from .embed import GameEmbedding

class Critic(Default):
  _options = [
    Option('critic_layers', type=int, nargs='+', default=[128, 128]),
    Option('critic_weight', type=float, default=.5),
    Option('gae_lambda', type=float, default=1., help="Generalized Advantage Estimation"),
    Option('fix_scopes', type=bool, default=False),
  ]
  
  _members = [
    ('rlConfig', RLConfig),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, input_size, scope='critic', **kwargs):
    Default.__init__(self, **kwargs)
    
    self.net = tfl.Sequential()
    with tf.variable_scope(scope):
      prev_size = input_size
      for i, next_size in enumerate(self.critic_layers):
        with tf.variable_scope("layer_%d" % i):
          self.net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      
      if self.fix_scopes:
        self.net.append(tfl.FCLayer(prev_size, 1))
    
    if not self.fix_scopes:
      with tf.variable_scope(scope):
        self.net.append(tfl.FCLayer(prev_size, 1))
    
    self.variables = self.net.getVariables()
  
  def __call__(self, inputs, rewards, prob_ratios, **unused):
    values = tf.squeeze(self.net(inputs), [-1])
    trainVs = values[:-1]
    lastV = values[-1]
    
    lambda_ = tf.minimum(1., prob_ratios) * self.gae_lambda
    targets = tfl.smoothed_returns(trainVs, rewards, self.rlConfig.discount, lambda_, lastV)
    targets = tf.stop_gradient(targets)
    advantages = targets - trainVs
    
    advantage_avg = tf.reduce_mean(advantages)
    tf.summary.scalar('advantage_avg', advantage_avg)
    tf.summary.scalar('advantage_std', tf.sqrt(tfl.sample_variance(advantages)))
    
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.summary.scalar('v_loss', vLoss)
    tf.summary.scalar("v_uev", vLoss / tfl.sample_variance(targets))
    
    return vLoss * self.critic_weight, targets, advantages

