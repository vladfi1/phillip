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

    Option('actor_learning_rate', type=float, default=1e-4),
  ]

  _members = [
    #('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, input_size, action_size, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.action_size = action_size
    self.rlConfig = rlConfig
    
    name = "actor"
    net = tfl.Sequential()
    with tf.variable_scope(name):
      prev_size = input_size
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

  def train_probs(self, history, actions):
    history = history[-self.rlConfig.memory-1:]
    delayed_actions = actions[:-1]
    input_ = tf.concat(axis=2, values=history + delayed_actions)
    actions = actions[-1]
    
    actor_probs = self.actor(input_)
    log_actor_probs = tf.log(actor_probs)

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.summary.scalar('entropy_avg', entropy_avg)
    tf.summary.scalar('entropy_min', tf.reduce_min(entropy))
    tf.summary.histogram('entropy', entropy)

    taken_probs = tfl.batch_dot(actions, actor_probs)
    taken_log_probs = tfl.batch_dot(actions, log_actor_probs)
    
    return taken_probs, taken_log_probs, entropy

  def train(self, taken_log_probs, advantages, entropy):
    actor_gain = taken_log_probs * tf.stop_gradient(advantages) + self.entropy_scale * entropy
    optimizer = tf.train.AdamOptimizer(self.actor_learning_rate)
    return optimizer.minimize(-actor_gain, var_list=self.getVariables())

  def getVariables(self):
    return self.actor.getVariables()
  
  def getPolicy(self, history, delayed_actions, **unused):
    history = history[-self.rlConfig.memory-1:]
    input_ = tf.concat(axis=0, values=history + tf.unstack(delayed_actions))
    return self.actor(input_)

  def act(self, policy, verbose=False):
    action = random.choice(range(self.action_size), p=policy)
    return action, policy[action], []

