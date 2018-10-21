import tensorflow as tf
from . import tf_lib as tfl, util, opt
from numpy import random
from .default import *
from .mutators import relative

class ActorCritic(Default):
  _options = [
    Option('actor_layers', type=int, nargs='+', default=[128, 128]),
    Option('fix_scopes', type=bool, default=False),

    Option('epsilon', type=float, default=0.02),

    Option('entropy_power', type=float, default=1),
    Option('entropy_scale', type=float, default=0.001),
    Option('evolve_entropy', action="store_true"),

    Option('actor_weight', type=float, default=1.),
  ]

  _members = [
    #('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, input_size, embedAction, rlConfig, **kwargs):
    Default.__init__(self, **kwargs)
    self.embedAction = embedAction
    self.action_set = list(range(embedAction.input_size))
    self.rlConfig = rlConfig
    self.evo_variables = []
    
    name = "actor"
    net = tfl.Sequential()
    with tf.variable_scope(name):
      prev_size = input_size
      for i, next_size in enumerate(getattr(self, name + "_layers")):
        with tf.variable_scope("layer_%d" % i):
          net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      
      if self.fix_scopes:
        net.append(tfl.FCLayer(prev_size, embedAction.size))
      
      if self.evolve_entropy:
        self.entropy_scale = tf.Variable(self.entropy_scale, trainable=False, name='entropy_scale')
        self.evo_variables.append(("entropy_scale", self.entropy_scale, relative(1.25)))
      
    if not self.fix_scopes:
      with tf.variable_scope('actor'):
        net.append(tfl.FCLayer(prev_size, embedAction.size))
    
    net.append(embedAction.to_input)  # softmax or dot-product + softmax
    net.append(lambda t: (1. - self.epsilon) * t + self.epsilon / embedAction.input_size)
    
    self.actor = net
  
  def train_probs(self, inputs, actions):
    delayed_actions = actions[:-1]
    inputs = tf.concat(axis=2, values=[inputs] + delayed_actions)
    actions = actions[-1]
    
    actor_probs = self.actor(inputs)
    log_actor_probs = tf.log(actor_probs)

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.summary.scalar('entropy_avg', entropy_avg)
    tf.summary.scalar('entropy_min', tf.reduce_min(entropy))
    #tf.summary.histogram('entropy', entropy)

    taken_probs = tfl.batch_dot(actions, actor_probs)
    taken_log_probs = tfl.batch_dot(actions, log_actor_probs)
    
    return taken_probs, taken_log_probs, entropy

  def train(self, taken_log_probs, advantages, entropy):
    actor_gain = taken_log_probs * tf.stop_gradient(advantages) + self.entropy_scale * entropy
    return -tf.reduce_mean(actor_gain) * self.actor_weight

  def getVariables(self):
    return self.actor.getVariables()
  
  def getPolicy(self, core_output, delayed_actions, **unused):
    delayed_actions = tf.reshape(delayed_actions, [1, -1])  # TODO: generalize
    input_ = tf.concat(axis=-1, values=[core_output, delayed_actions])
    return self.actor(input_)

  def act(self, policy, verbose=False):
    action = random.choice(self.action_set, p=policy)
    return action, policy[action]

