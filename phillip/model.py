import itertools
import tensorflow as tf
from .default import *
from . import embed, ssbm, tf_lib as tfl, util
from .rl_common import *

class Model(Default):
  _options = [
    Option("model_layers", type=int, nargs='+', default=[256]),

    Option('model_weight', type=float, default=1.),
    Option('predict_steps', type=int, default=1, help="number of future frames to predict"),
    Option('dynamic', type=int, default=1, help='use dynamic loop unrolling'),
  ]
  
  _members = [
    ('nl', tfl.NL),
  ]
  
  def __init__(self, embedGame, action_size, core, config, scope="model", **kwargs):
    Default.__init__(self, **kwargs)
    self.embedGame = embedGame
    self.rlConfig = config
    self.action_size = action_size
    self.core = core
    
    self.input_size = core.output_size + action_size
    self.while_loop = tf.while_loop if self.dynamic else tfl.while_loop
        
    with tf.variable_scope(scope):
      net = tfl.Sequential()
      
      prev_size = self.input_size
      
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

  def apply(self, inputs, last):
    outputs = self.net(inputs)
    
    delta = self.delta_layer(outputs)
    new = self.new_layer(outputs)
    forget = self.forget_layer(outputs)
    
    return forget * (last + delta) + (1. - forget) * new
  
  def distances(self, history, core_outputs, hidden_states, actions, raw_state,
    predict_steps, **unused):
    """Computes the model's loss on a given set of transitions.
    
    Args:
      history: List of game states from past to present, of length M+1. Each element is a tensor of shape [T-M, B, F].
        The states with valid histories are indexed [M, T).
      core_outputs: Outputs from the agent Core, of shape [T-M, B, O).
      hidden_states: Structure of state Tensors of shape [T-M, B, S).
      actions: Integer tensor of actions taken, of shape [T-M, B], corresponding to times [M, T).
      raw_state: Unembedded state structure of shape [T, B] tensors. Used for getting the first residual state.
      predict_steps: Number of steps to predict.
    
    Returns:
      A GameMemory-shaped structure of distances - tensors of shape [P, T-M-P, B] 
    """
    memory = self.rlConfig.memory
    length = self.rlConfig.experience_length - memory - predict_steps

    cut = (lambda t: t[:-predict_steps]) if predict_steps > 0 else (lambda t: t)
    history = [cut(h) for h in history]
    core_outputs = cut(core_outputs)
    hidden_states = util.deepMap(cut, hidden_states)
    current_actions = tfl.windowed(actions, predict_steps)
    
    states = util.deepMap(lambda t: tfl.windowed(t[memory:], predict_steps), raw_state)
    begin_states = util.deepMap(lambda t: t[0], states)
    target_states = util.deepMap(lambda t: t[1:], states)
    
    last_states = self.embedGame(begin_states, residual=True)
    ta_fn = tf.TensorArray if self.dynamic else tfl.TensorArray
    predicted_ta = ta_fn(last_states.dtype, size=predict_steps, element_shape=last_states.get_shape())
    
    def predict_step(i, prev_history, prev_core, prev_hidden, prev_state, predicted_ta):
      current_action = current_actions[i]
      inputs = tf.concat(axis=-1, values=[prev_core] + [current_action])
      
      predicted_state = self.apply(inputs, prev_state)
      
      next_state = self.embedGame.to_input(predicted_state)
      next_combined = tf.concat(axis=-1, values=[next_state, current_action])
      next_history = prev_history[1:] + [next_combined]
      next_input = tf.concat(axis=-1, values=next_history)
      next_core, next_hidden = self.core(next_input, prev_hidden)
    
      predicted_ta = predicted_ta.write(i, predicted_state)
      return i+1, next_history, next_core, next_hidden, predicted_state, predicted_ta
    
    loop_vars = (0, history, core_outputs, hidden_states, last_states, predicted_ta)
    cond = lambda i, *_: i < predict_steps
    _, _, final_core_outputs, _, _, predicted_ta = self.while_loop(cond, predict_step, loop_vars)
    predicted_states = predicted_ta.stack()
    predicted_states.set_shape([predict_steps, length, None, self.embedGame.size])
    
    distances = self.embedGame.distance(predicted_states, target_states)
    return distances, final_core_outputs

  def train(self, history, core_outputs, hidden_states, actions, raw_state, **unused):
    distances, final_core_outputs = self.distances(history, core_outputs, hidden_states, actions, raw_state, self.predict_steps)
    distances = util.deepMap(lambda t: tf.reduce_mean(t, [1, 2]), distances)
    total_distances = tf.add_n(list(util.deepValues(distances)))
    for step in range(self.predict_steps):
      # log all the individual distances
      for path, tensor in util.deepItems(distances):
        tag = "model/%d/" % step + "/".join(map(str, path))
        tf.summary.scalar(tag, tensor[step])
    
      tf.summary.scalar("model/%d/total" % step, total_distances[step])
    
    total_distance = tf.reduce_mean(total_distances) * self.model_weight
    return total_distance, final_core_outputs
  
  def predict(self, history, core_outputs, hidden_states, actions, raw_state):
    last_state = util.deepMap(lambda t: t[-1], raw_state)
    last_state = self.embedGame(last_state, residual=True)

    def predict_step(i, prev_history, prev_core, prev_hidden, prev_state):
      current_action = actions[:, i]
      inputs = tf.concat(axis=-1, values=[prev_core, current_action])
      
      predicted_state = self.apply(inputs, prev_state)
      
      next_state = self.embedGame.to_input(predicted_state)
      next_combined = tf.concat(axis=-1, values=[next_state, current_action])
      next_history = prev_history[1:] + [next_combined]
      next_input = tf.concat(axis=-1, values=next_history)
      next_core, next_hidden = self.core(next_input, prev_hidden)

      return i+1, next_history, next_core, next_hidden, predicted_state

    loop_vars = (0, history, core_outputs, hidden_states, last_state)
    cond = lambda i, *_: i < self.predict_steps
    _, _, predicted_core_outputs, _, _ = self.while_loop(cond, predict_step, loop_vars)
    return predicted_core_outputs

