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
    
    self.net = net
  
  def epsilon_greedy(self, probs):
    return (1. - self.epsilon) * probs + self.epsilon / self.embedAction.input_size
  
  def get_probs(self, inputs, delayed_actions):
    """Computes probabilites for the actor.
    
    B is Batch dim/shape, can have rank > 1
    C is Core output dim
    E is action Embed dim
    D is number of Delay steps
    A is number of Actions
    
    Args:
      inputs: Tensor of shape [B, C]
      delayed_actions: list of D tensors with shapes [B, E].
    Returns:
      Tensor of shape [B, A] with action probabilities.
    """
    
    inputs = tf.concat(axis=-1, values=[inputs] + delayed_actions)
    net_outputs = self.net(inputs)
    # FIXME: to_input is the wrong method. Should be embed_to_probs
    probs = self.embedAction.to_input(net_outputs)
    return self.epsilon_greedy(probs)
  
  def train_probs(self, inputs, delayed_actions, taken_action):
    actor_probs = self.get_probs(inputs, delayed_actions)
    log_actor_probs = tf.log(actor_probs)

    entropy = - tfl.batch_dot(actor_probs, log_actor_probs)
    entropy_avg = tfl.power_mean(self.entropy_power, entropy)
    tf.summary.scalar('entropy_avg', entropy_avg)
    tf.summary.scalar('entropy_min', tf.reduce_min(entropy))
    #tf.summary.histogram('entropy', entropy)

    actions_1hot = tf.one_hot(taken_action, len(self.action_set))
    taken_probs = tfl.batch_dot(actions_1hot, actor_probs)
    taken_log_probs = tfl.batch_dot(actions_1hot, log_actor_probs)
    
    return taken_probs, taken_log_probs, entropy

  def train(self, taken_log_probs, advantages, entropy):
    actor_gain = taken_log_probs * tf.stop_gradient(advantages) + self.entropy_scale * entropy
    return -tf.reduce_mean(actor_gain) * self.actor_weight

  def getVariables(self):
    return self.net.getVariables()
  
  def getPolicy(self, core_output, delayed_actions, **unused):
    delayed_actions = tf.unstack(delayed_actions, axis=1)
    return self.get_probs(core_output, delayed_actions)

  def act(self, policy, verbose=False):
    action = random.choice(self.action_set, p=policy)
    return action, policy[action]

