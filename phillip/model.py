from collections import namedtuple
import itertools
import tensorflow as tf
from .default import *
from . import embed, ssbm, tf_lib as tfl, util
from .rl_common import *

nest = tf.contrib.framework.nest

ModelInput = namedtuple("ModelInput", "history core_output hidden_state residual")

class Model(Default):
  _options = [
    Option("model_layers", type=int, nargs='+', default=[256]),

    Option('model_weight', type=float, default=1.),
    Option('predict_steps', type=int, default=1, help="number of future frames to predict"),
    Option('extra_steps', type=int, default=0, help="extra future frames to predict"),
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
  
  def distances(self, model_inputs, actions, raw_states, predict_steps, aux_losses={}):
    """Computes the model's loss on a given set of transitions.
    
    Args:
      model_inputs: ModelInput tuple with shapes [T, B, ...]
      actions: Embedded actions taken, of shape [T, B, A].
      raw_states: Unembedded state structure of shape [T, B] tensors.
      predict_steps: Number of steps to predict.
      aux_losses: Each auxiliary loss is a function that takes predicted core output and target core output, returning a scalar distance between them.
    
    Returns:
      A GameMemory-shaped structure of distances - tensors of shape [P, T-M-P, B] 
    """
    target_fn = lambda t: tfl.windowed(t, predict_steps)[1:]
    target_states = util.deepMap(target_fn, raw_states)
    target_core_outputs = target_fn(model_inputs.core_output)

    # prepare for prediction loop (scan)
    cut = (lambda t: t[:-predict_steps]) if predict_steps > 0 else (lambda t: t)
    model_inputs = nest.map_structure(cut, model_inputs)
    current_actions = tfl.windowed(actions, predict_steps)[:-1]
    
    scan = tf.scan if self.dynamic else tfl.scan
    predicted_outputs = scan(self.predict_step, current_actions, model_inputs)
    
    distances = self.embedGame.distance(predicted_outputs.residual, target_states)
    for k, f in aux_losses.items():
      distances[k] = f(predicted_outputs.core_output, target_core_outputs)
    return distances, predicted_outputs

  def train(self, history, core_outputs, hidden_states, actions, raw_states, **kwargs):
    residual_states = self.embedGame(raw_states, residual=True)
    
    model_inputs = ModelInput(history, core_outputs, hidden_states, residual_states)
    distances, predicted_outputs = self.distances(model_inputs, actions, raw_states, self.predict_steps, **kwargs)
    
    distances = util.deepMap(lambda t: tf.reduce_mean(t, [1, 2]), distances)
    total_distances = tf.add_n(list(util.deepValues(distances)))
    for step in range(self.predict_steps):
      # log all the individual distances
      for path, tensor in util.deepItems(distances):
        tag = "model/%d/" % step + "/".join(map(str, path))
        tf.summary.scalar(tag, tensor[step])
    
      tf.summary.scalar("model/%d/total" % step, total_distances[step])
    
    total_distance = tf.reduce_mean(total_distances) * self.model_weight
    return total_distance, predicted_outputs.core_output[-1]
  
  def predict_step(self, prev_input, action):
    prev_history, prev_core, prev_hidden, prev_state = prev_input
    inputs = tf.concat(axis=-1, values=[prev_core, action])
    
    predicted_state = self.apply(inputs, prev_state)
    
    next_state = self.embedGame.to_input(predicted_state)
    next_combined = tf.concat(axis=-1, values=[next_state, action])
    next_history = prev_history[1:] + [next_combined]
    next_input = tf.concat(axis=-1, values=next_history)
    next_core, next_hidden = self.core(next_input, prev_hidden)

    return ModelInput(next_history, next_core, next_hidden, predicted_state)

  def predict(self, history, core_outputs, hidden_states, actions, residual_state):
    def predict_step(i, prev_inputs):
      return i+1, self.predict_step(prev_inputs, actions[:, i])

    loop_vars = (0, ModelInput(history, core_outputs, hidden_states, residual_state))
    cond = lambda i, _: i < self.predict_steps
    return tf.while_loop(cond, predict_step, loop_vars)[1]

