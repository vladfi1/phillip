import itertools
import tensorflow as tf
from .default import *
from . import embed, ssbm, tf_lib as tfl, util
from .rl_common import *

class Model(Default):
  _options = [
    Option("model_layers", type=int, nargs='+', default=[256]),

    Option('action_type', type=str, default="diagonal", choices=ssbm.actionTypes.keys()),
    Option('model_learning_rate', type=float, default=1e-4),
    Option('predict_steps', type=int, default=1, help="number of future frames to predict")
  ]
  
  _members = [
    ('embedGame', embed.GameEmbedding),
    ('nl', tfl.NL),
    ('rlConfig', RLConfig),
  ]
  
  def __init__(self, scope="model", **kwargs):
    Default.__init__(self, **kwargs)
    
    self.actionType = ssbm.actionTypes[self.action_type]
    action_size = self.actionType.size # TODO: use the actual controller embedding
    self.embedAction = embed.OneHotEmbedding("action", action_size)
    
    history_size = (1+self.rlConfig.memory) * (self.embedGame.size + action_size)
    input_size = action_size + history_size
    
    with tf.variable_scope(scope):
      net = tfl.Sequential()
      
      prev_size = input_size
      
      for i, next_size in enumerate(self.model_layers):
        with tf.variable_scope("layer_%d" % i):
          net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      
      with tf.variable_scope("output"):
        self.delta_layer = tfl.FCLayer(prev_size, self.embedGame.size, bias_init=tfl.constant_init(0.))
        self.new_layer = tfl.FCLayer(prev_size, self.embedGame.size)
        self.forget_layer = tfl.FCLayer(prev_size, self.embedGame.size, nl=tf.sigmoid, bias_init=tfl.constant_init(1.))
      
      self.net = net
    
    layers = [self.net, self.delta_layer, self.new_layer, self.forget_layer]
    self.variables = list(itertools.chain.from_iterable([l.getVariables() for l in layers]))
  
  def getVariables(self):
    return self.variables

  def apply(self, history, last):
    outputs = self.net(history)
    
    delta = self.delta_layer(outputs)
    new = self.new_layer(outputs)
    forget = self.forget_layer(outputs)
    
    return forget * (last + delta) + (1. - forget) * new
  
  def train(self, state, action, prev_action, **unused):
    states = self.embedGame(state)
    prev_actions = self.embedAction(prev_action)
    combined = tf.concat(2, [states, prev_actions])
    actions = self.embedAction(action)
    
    memory = self.rlConfig.memory
    length = combined.get_shape()[-2].value - memory
    history = [tf.slice(combined, [0, i, 0], [-1, length, -1]) for i in range(memory+1)]

    residuals = self.embedGame(state, residual=True)
    last_states = residuals[:,memory:,:]

    totals = []

    for step in range(self.predict_steps):
      # remove last time step from histories
      history = [t[:,:-1,:] for t in history]
      last_states = last_states[:,:-1,:]
      
      # stack memory frames and current action
      history_concat = tf.concat(2, history[step:])
      current_action = actions[:,memory+step:-1,:]
      inputs = tf.concat(2, [history_concat, current_action])
      
      predicted_states = self.apply(inputs, last_states)
      
      # prepare for the next frame
      last_states = predicted_states
      next_actions = prev_actions[:,memory+step+1:,:]
      next_inputs = self.embedGame.to_input(predicted_states)
      history.append(tf.concat(2, [next_inputs, next_actions]))
      
      # compute losses on this frame
      target_states = util.deepMap(lambda t: t[:,memory+1+step:], state)
    
      distances = self.embedGame.distance(predicted_states, target_states)
      distances = util.deepMap(tf.reduce_mean, distances)
      
      # log all the individual distances
      for path, tensor in util.deepItems(distances):
        tag = "model/%d/" % step + "/".join(map(str, path))
        tf.scalar_summary(tag, tensor)
    
      total = tf.add_n(list(util.deepValues(distances)))
      tf.scalar_summary("model/%d/total" % step, total)
      totals.append(total)
    
    total_distance = tf.add_n(totals)
    return tf.train.AdamOptimizer(self.model_learning_rate).minimize(total_distance)
  
  """
  def predict(self, experience, action, extract=False):
    input = tf.concat(0, [history, action])
    output = self.apply(input)
    
    if extract:
      output = embedGame.extract(output)
    
    return output
  """
