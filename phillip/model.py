import itertools
import tensorflow as tf
from .default import *
from . import embed, ssbm, RL, tf_lib as tfl, util

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
    ('rlConfig', RL.RLConfig),
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.actionType = ssbm.actionTypes[self.action_type]
    action_size = self.actionType.size # TODO: use the actual controller embedding
    self.embedAction = embed.OneHotEmbedding("action", action_size)
    
    history_size = (1+self.rlConfig.memory) * (embedGame.size + action_size)
    input_size = action_size + history_size
    
    with tf.variable_scope("model"):
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
  
  def train(self, experiences):
    states = embedGame(experiences['state'])
    prev_actions = self.embedAction(experiences['prev_action'])
    
    delay_length = self.rlConfig.experience_length - self.rlConfig.delay
    train_length = delay_length - self.rlConfig.memory - 1
    
    delayed_states = states[:,self.rlConfig.delay:,:]
    prev_actions = prev_actions[:,:delay_length,:]
    combined_states = tf.concat(2, [delayed_states, prev_actions])
    
    histories = [tf.slice(combined_states, [0, i, 0], [-1, train_length, -1]) for i in range(self.rlConfig.memory+1)]
    histories = tf.concat(2, histories)
    
    actions = self.embedAction(experiences['action'])
    train_actions = tf.slice(actions, [0, self.rlConfig.memory, 0], [-1, train_length, -1])
    
    inputs = tf.concat(2, [histories, train_actions])
    
    last_states = delayed_states[:,self.rlConfig.memory:-1,:]
    
    predicted_states = self.apply(inputs, last_states)
    
    target_states = util.deepMap(lambda t: t[:,-train_length:], experiences['state'])
    
    distances = embedGame.distance(predicted_states, target_states)
    #distances = util.deepValues(distances)
    distances = util.deepMap(tf.reduce_mean, distances)
    
    tf.scalar_summary("model/loss/self_x", tf.sqrt(distances['players'][1]['x']))
    tf.scalar_summary("model/loss/action_state", distances['players'][1]['action_state'])
    
    distance = tf.add_n(list(util.deepValues(distances)))
    tf.scalar_summary("model/loss/total", distance)
    
    return tf.train.AdamOptimizer(self.model_learning_rate).minimize(distance)
  
  def predict(self, history, action, extract=False):
    input = tf.concat(0, [history, action])
    output = self.apply(input)
    
    if extract:
      output = embedGame.extract(output)
    
    return output

