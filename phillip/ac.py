import tensorflow as tf
from . import tf_lib as tfl, util, opt
from . import rl_common as RL
from numpy import random
from .default import *

class ActorCritic(Default):
  hidden_size = []
  
  _options = [
    Option('actor_layers', type=int, nargs='+', default=[128, 128]),
    Option('fix_scopes', type=bool, default=False),

    Option('epsilon', type=float, default=0.02),

    Option('entropy_power', type=float, default=1),
    Option('entropy_scale', type=float, default=0.001),
  ]

  _members = [
    ('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, embedGame, embedAction, global_step, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.rlConfig = rlConfig
    
    self.embedGame = embedGame
    self.embedAction = embedAction
    action_size = embedAction.size
    
    history_size = (1+rlConfig.memory) * (embedGame.size+embedAction.size)
    
    name = "actor"
    net = tfl.Sequential()
    with tf.variable_scope(name):
      prev_size = history_size
      for i, next_size in enumerate(getattr(self, name + "_layers")):
        with tf.variable_scope("layer_%d" % i):
          net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      
      if self.fix_scopes:
        net.append(tfl.FCLayer(prev_size, action_size, lambda p: (1. - self.epsilon) * tf.nn.softmax(p) + self.epsilon / action_size))
      
    if not self.fix_scopes:
      with tf.variable_scope('actor'):
        net.append(tfl.FCLayer(prev_size, action_size, lambda p: (1. - self.epsilon) * tf.nn.softmax(p) + self.epsilon / action_size))
    
    self.actor = net

  def train(self, state, prev_action, action, advantages, **unused):
    embedded_state = self.embedGame(state)
    embedded_prev_action = self.embedAction(prev_action)
    history = RL.makeHistory(embedded_state, embedded_prev_action, self.rlConfig.memory)
    
    actor_probs = self.actor(history)
    log_actor_probs = tf.log(actor_probs)

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.scalar_summary('entropy_avg', entropy_avg)
    tf.scalar_summary('entropy_min', tf.reduce_min(entropy))
    tf.histogram_summary('entropy', entropy)

    actions = self.embedAction(action[:,self.rlConfig.memory:])
    real_log_actor_probs = tfl.batch_dot(actions, log_actor_probs)
    train_log_actor_probs = real_log_actor_probs[:,:-1] # last state has no advantage
    actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))
    #tf.scalar_summary('actor_gain', actor_gain)
    
    actor_loss = - (actor_gain + self.entropy_scale * entropy_avg)
    
    actor_params = self.actor.getVariables()
      
    def metric(p1, p2):
      return tf.reduce_mean(tfl.kl(p1, p2))
    
    return self.optimizer.optimize(actor_loss, actor_params, log_actor_probs, metric)
  
  def getPolicy(self, state, **unused):
    return self.actor(state)

  def act(self, policy, verbose=False):
    action = random.choice(range(self.embedAction.size), p=policy)
    return action, policy[action], []

