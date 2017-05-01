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
    Option('retrace', type=bool, default=True, help="Retrace(lambda) - correct for off-policy behavior"),
  ]
  
  _members = [
    ('rlConfig', RLConfig),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, embedGame, embedAction, scope='critic', **kwargs):
    Default.__init__(self, **kwargs)
    
    self.embedGame = embedGame
    self.embedAction = embedAction
    history_size = (1+self.rlConfig.memory) * (embedGame.size+embedAction.size)
    
    self.net = tfl.Sequential()
    with tf.variable_scope(scope):
      prev_size = history_size
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
  
  def __call__(self, state, prev_action, reward, ratios, **unused):
    embedded_state = self.embedGame(state)
    embedded_prev_action = self.embedAction(prev_action)
    history = makeHistory(embedded_state, embedded_prev_action, self.rlConfig.memory)

    values = tf.squeeze(self.net(history), [-1])
    trainVs = values[:,:-1]
    # lastV = values[:,-1]
    
    rewards = reward[:,self.rlConfig.memory:]
    deltaVs = rewards + self.rlConfig.discount * values[:,1:] - trainVs
    
    if self.retrace:
      discounts = tf.minimum(1., ratios[:,:-1])
    else:
      discounts = tf.ones_like(trainVs)
    
    discounts *= self.rlConfig.discount * self.gae_lambda
    advantages = tfl.discount2(deltaVs, discounts)

    targets = trainVs + advantages
    # targets = tfl.discount2(rewards, self.rlConfig.discount, lastV)
    targets = tf.stop_gradient(targets)
    
    # advantages = targets - trainVs
    advantage_avg = tf.reduce_mean(advantages)
    tf.scalar_summary('advantage_avg', advantage_avg)
    tf.scalar_summary('advantage_std', tf.sqrt(tfl.sample_variance(advantages)))
    
    vLoss = tf.reduce_mean(tf.square(advantages))
    tf.scalar_summary('v_loss', vLoss)
    tf.scalar_summary("v_uev", vLoss / tfl.sample_variance(targets))
    
    opt = tf.train.AdamOptimizer(self.critic_learning_rate)

    # need to negate gradients since the optimizer negates again
    grads = tf.gradients(trainVs, self.variables, grad_ys=-advantages)
    train_op = opt.apply_gradients(zip(grads, self.variables))
    # train_op = opt.minimize(vLoss, var_list=self.variables)
    
    return train_op, targets, advantages

