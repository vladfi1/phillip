import itertools
import tensorflow as tf
from .default import *
from . import embed, ssbm, tf_lib as tfl, util
from .rl_common import *

class Model(Default):
  _options = [
    Option("model_layers", type=int, nargs='+', default=[256]),

    Option('model_learning_rate', type=float, default=1e-4),
    Option('predict_steps', type=int, default=1, help="number of future frames to predict"),
    Option('predict_scale', type=float, default=1., help="scale incoming gradients"),
  ]
  
  _members = [
    ('nl', tfl.NL),
  ]
  
  def __init__(self, embedGame, action_size, config, scope="model", **kwargs):
    Default.__init__(self, **kwargs)
    self.embedGame = embedGame
    self.rlConfig = config
    
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
  
  def train(self, history, actions, state, **unused):
    memory = self.rlConfig.memory
    length = self.rlConfig.experience_length - memory

    state = util.deepMap(lambda t: t[:,memory:], state)
    last_states = self.embedGame(state, residual=True)

    totals = []

    for step in range(self.predict_steps):
      # remove last time step from histories
      history = [t[:,:-1] for t in history]
      last_states = last_states[:,:-1]
      
      # stack memory frames and current action
      # history_concat = tf.concat(2, history[step:])
      current_action = actions[:,step:-1]
      inputs = tf.concat(axis=2, values=history[step:] + [current_action])
      
      predicted_states = self.apply(inputs, last_states)
      
      # prepare for the next frame
      last_states = predicted_states
      # next_actions = prev_actions[:,memory+step+1:,:]
      next_inputs = self.embedGame.to_input(predicted_states)
      history.append(tf.concat(axis=2, values=[next_inputs, current_action]))
      
      # compute losses on this frame
      target_states = util.deepMap(lambda t: t[:,1+step:], state)
      # predictions = predicted_states[:,:-1-step]
      distances = self.embedGame.distance(predicted_states, target_states)
      distances = util.deepMap(tf.reduce_mean, distances)
      
      # log all the individual distances
      for path, tensor in util.deepItems(distances):
        tag = "model/%d/" % step + "/".join(map(str, path))
        tf.summary.scalar(tag, tensor)
    
      total = tf.add_n(list(util.deepValues(distances)))
      tf.summary.scalar("model/%d/total" % step, total)
      totals.append(total)

    #history = [tfl.scale_gradient(h, self.predict_scale) for h in history]
    
    total_distance = tf.add_n(totals)
    #loss = total_distance * self.model_learning_rate
    self.opt = tf.train.AdamOptimizer(self.model_learning_rate)
    train_op = self.opt.minimize(total_distance, var_list=self.variables)
    return train_op, history
  
  def predict(self, history, actions, raw_state):
    last_state = util.deepMap(lambda t: t[-1], raw_state)
    last_state = self.embedGame(last_state, residual=True)

    for step, action in enumerate(tf.unstack(actions)):
      input_ = tf.concat(axis=0, values=history[step:] + [action])
      predicted_state = self.apply(input_, last_state)
      
      # prepare for the next frame
      last_state = predicted_state
      next_input = self.embedGame.to_input(predicted_state)
      history.append(tf.concat(axis=0, values=[next_input, action]))
    
    return history
