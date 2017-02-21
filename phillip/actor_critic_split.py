import tensorflow as tf
import tf_lib as tfl
import util
from numpy import random

class ActorCriticSplit:
  def __init__(self, state_size, action_size, global_step, rlConfig, **kwargs):
    self.action_size = action_size
    self.layer_sizes = [128, 128]
    self.layers = []

    self.actor = tfl.Sequential()
    self.critic = tfl.Sequential()
    
    prev_size = state_size
    for i, next_size in enumerate(self.layer_sizes):
      for net in ['actor', 'critic']:
        with tf.variable_scope("%s/layer_%d" % (net, i)):
          getattr(self, net).append(tfl.makeAffineLayer(prev_size, next_size, tfl.leaky_softplus()))
      prev_size = next_size

    with tf.variable_scope('actor'):
      actor = tfl.makeAffineLayer(prev_size, action_size, tf.nn.log_softmax)
      self.actor.append(actor)

    with tf.variable_scope('critic'):
      v_out = tfl.makeAffineLayer(prev_size, 1)
      v_out = util.compose(lambda x: tf.squeeze(x, [-1]), v_out)
      self.critic.append(v_out)

    self.rlConfig = rlConfig

  def getLoss(self, states, actions, rewards, entropy_scale=0.01, policy_scale=1.0, **kwargs):
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
    
    self.policy_scale = tf.Variable(policy_scale)
    
    min_rate = 1e-8
    max_rate = 1e2
    
    self.decrease_policy_scale = tf.assign(self.policy_scale, tf.maximum(min_rate, self.policy_scale / 1.5))
    self.increase_policy_scale = tf.assign(self.policy_scale, tf.minimum(max_rate, self.policy_scale * 1.5))
    
    acLoss = vLoss - self.policy_scale * (actor_gain + entropy_scale * actor_entropy)
    
    stats = [
      ('vLoss', vLoss),
      ('actor_gain', actor_gain),
      ('actor_entropy', actor_entropy),
      ('policy_scale', tf.log(self.policy_scale))
    ]

    return acLoss, stats, log_actor_probs
  
  def getPolicy(self, state, **kwargs):
    return tf.exp(self.actor(state))

  def act(self, policy, verbose=False):
    return random.choice(range(self.action_size), p=policy)
