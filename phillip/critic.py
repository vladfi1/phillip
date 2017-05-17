import tensorflow as tf
from . import tf_lib as tfl
from .default import *
from .rl_common import *
#from .embed import GameEmbedding

class Critic(Default):
  _options = [
    Option('critic_layers', type=int, nargs='+', default=[128, 128]),
    Option('critic_learning_rate', type=float, default=1e-4),
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
  
  def __call__(self, history, rewards, **unused):
    history = history[-self.rlConfig.memory-1:]
    input_ = tf.concat(axis=2, values=history)

    values = tf.squeeze(self.net(input_), [-1])
    trainVs = values[:,:-1]
    # lastV = values[:,-1]
    
    deltaVs = rewards + self.rlConfig.discount * values[:,1:] - trainVs
    advantages = tfl.discount2(deltaVs, self.rlConfig.discount * self.gae_lambda)

    targets = trainVs + advantages
    # targets = tfl.discount2(rewards, self.rlConfig.discount, lastV)
    targets = tf.stop_gradient(targets)
    
    # advantages = targets - trainVs
    advantage_avg = tf.reduce_mean(advantages)
    tf.summary.scalar('advantage_avg', advantage_avg)
    tf.summary.scalar('advantage_std', tf.sqrt(tfl.sample_variance(advantages)))
    
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.summary.scalar('v_loss', vLoss)
    tf.summary.scalar("v_uev", vLoss / tfl.sample_variance(targets))
    
    opt = tf.train.AdamOptimizer(self.critic_learning_rate)

    # need to negate gradients since the optimizer negates again
    grads = tf.gradients(trainVs, self.variables, grad_ys=-advantages)
    train_op = opt.apply_gradients(zip(grads, self.variables))
    # train_op = opt.minimize(vLoss, var_list=self.variables)
    
    return train_op, targets, advantages

