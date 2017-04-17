import itertools
import tensorflow as tf
from .default import *
from . import embed, ssbm, tf_lib as tfl, util
from .rl_common import *

# parameter-less embedding
embedGame = embed.GameEmbedding()

class Model(Default):
  _options = [
    Option("model_layers", type=int, nargs='+', default=[128]),

    Option('action_type', type=str, default="diagonal", choices=ssbm.actionTypes.keys()),
    Option('model_learning_rate', type=float, default=1e-4),
  ]
  
  _members = [
    ('nl', tfl.NL),
    ('rlConfig', RLConfig),
  ]
  
  def __init__(self, scope="model", **kwargs):
    Default.__init__(self, **kwargs)
    
    self.actionType = ssbm.actionTypes[self.action_type]
    action_size = self.actionType.size # TODO: use the actual controller embedding
    self.embedAction = embed.OneHotEmbedding("action", action_size)
    
    history_size = (1+self.rlConfig.memory) * (embedGame.size + action_size)
    input_size = action_size + history_size
    
    with tf.variable_scope(scope):
      net = tfl.Sequential()
      
      prev_size = input_size
      
      for i, next_size in enumerate(self.model_layers):
        with tf.variable_scope("layer_%d" % i):
          net.append(tfl.FCLayer(prev_size, next_size, self.nl))
        prev_size = next_size
      
      with tf.variable_scope("output"):
        self.delta_layer = tfl.FCLayer(prev_size, embedGame.size, bias_init=tfl.constant_init(0.))
        self.new_layer = tfl.FCLayer(prev_size, embedGame.size)
        self.forget_layer = tfl.FCLayer(prev_size, embedGame.size, nl=tf.sigmoid, bias_init=tfl.constant_init(1.))
      
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
    states = embedGame(state)
    prev_actions = self.embedAction(prev_action)

    histories = makeHistory(states, prev_actions, self.rlConfig.memory)
    
    actions = self.embedAction(action)
    train_actions = actions[:,self.rlConfig.memory:,:]
    
    inputs = tf.concat(2, [histories, train_actions])
    inputs = inputs[:,:-1,:] # last history has no target
    
    last_states = states[:,self.rlConfig.memory:-1,:]
    
    predicted_states = self.apply(inputs, last_states)
    
    target_states = util.deepMap(lambda t: t[:,self.rlConfig.memory + 1:], state)
    
    distances = embedGame.distance(predicted_states, target_states)
    #distances = util.deepValues(distances)
    distances = util.deepMap(tf.reduce_mean, distances)
    
    for path, tensor in util.deepItems(distances):
      tag = "model/loss/" + "/".join(map(str, path))
      tf.scalar_summary(tag, tensor)
    
    #tf.scalar_summary("model/loss/self_x", tf.sqrt(distances['players'][1]['x']))
    #tf.scalar_summary("model/loss/action_state", distances['players'][1]['action_state'])
    
    distance = tf.add_n(list(util.deepValues(distances)))
    tf.scalar_summary("model/loss/total", distance)
    
    return tf.train.AdamOptimizer(self.model_learning_rate).minimize(distance)
  
  """
  def predict(self, experience, action, extract=False):
    input = tf.concat(0, [history, action])
    output = self.apply(input)
    
    if extract:
      output = embedGame.extract(output)
    
    return output
  """
