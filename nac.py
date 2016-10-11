import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random
import natgrad
from default import *

class NaturalActorCritic(Default):
  _options = [
    Option('actor_layers', type=int, nargs='+', default=[128, 128]),
    Option('critic_layers', type=int, nargs='+', default=[128, 128]),

    Option('learning_rate', type=float, default=0.0005),
    Option('entropy_scale', type=float, default=0.001),
    Option('policy_scale', type=float, default=0.1),
    Option('kl_scale', type=float, default=1.0),
  ]
  
  _members = [
    ('natgrad', natgrad.NaturalGradient)
  ]
  
  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    super(NaturalActorCritic, self).__init__(**kwargs)
    
    self.action_size = action_size

    for name in ['actor', 'critic']:
      net = tfl.Sequential()
      with tf.variable_scope(name):
        prev_size = state_size
        for i, next_size in enumerate(getattr(self, name + "_layers")):
          with tf.variable_scope("layer_%d" % i):
            net.append(tfl.makeAffineLayer(prev_size, next_size, tfl.leaky_softplus()))
          prev_size = next_size
      setattr(self, name, net)

    with tf.variable_scope('actor'):
      actor = tfl.makeAffineLayer(prev_size, action_size, tf.nn.log_softmax)
      self.actor.append(actor)

    with tf.variable_scope('critic'):
      v_out = tfl.makeAffineLayer(prev_size, 1)
      v_out = util.compose(lambda x: tf.squeeze(x, [-1]), v_out)
      self.critic.append(v_out)

    self.rlConfig = rlConfig

  def train(self, states, actions, rewards):
    n = self.rlConfig.tdN
    
    state_shape = tf.shape(states)
    state_rank = tf.shape(state_shape)[0]
    experience_length = tf.gather(state_shape, state_rank-2)
    
    train_length = experience_length - n

    values = self.critic(states)
    log_actor_probs = self.actor(states)
    actor_probs = tf.exp(log_actor_probs)
    
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
    vLoss = tf.reduce_mean(tf.square(advantages))

    actor_entropy = -tf.reduce_mean(tfl.batch_dot(actor_probs, log_actor_probs))
    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = tf.slice(real_log_actor_probs, [0, 0], [-1, train_length])
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))
    
    acLoss = vLoss - self.policy_scale * (actor_gain + self.entropy_scale * actor_entropy)
    acLoss *= -self.learning_rate
    
    params = tf.trainable_variables()
    pg = tf.gradients(acLoss, params)
    
    predictions = [values, log_actor_probs]
    
    def metric(vp1, vp2):
      v1, p1 = vp1
      v2, p2 = vp2
      
      vDist = tf.reduce_mean(tf.squared_difference(v1, v2))
      pDist = tf.reduce_mean(tfl.kl(p1, p2))
      return vDist + self.kl_scale * pDist
    
    ng = self.natgrad(params, pg, predictions, metric)
    
    train_op = tf.group(*[tf.assign_add(p, g) for p, g in zip(params, ng)])
    
    stats = [
      ('vLoss', vLoss),
      ('actor_gain', actor_gain),
      ('actor_entropy', actor_entropy),
      #('policy_scale', tf.log(self.policy_scale))
    ]
    
    for name, tensor in stats:
      tf.scalar_summary(name, tensor)

    return train_op
  
  def getPolicy(self, state, **kwargs):
    return tf.exp(self.actor(state))

  def act(self, policy, verbose=False):
    return random.choice(range(self.action_size), p=policy)
