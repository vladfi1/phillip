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
    self.action_size = action_size
    
    history_size = (1+self.rlConfig.memory) * (self.embedGame.size + action_size)
    self.input_size = history_size + action_size
    
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

  def apply(self, history, last):
    outputs = self.net(history)
    
    delta = self.delta_layer(outputs)
    new = self.new_layer(outputs)
    forget = self.forget_layer(outputs)
    
    return forget * (last + delta) + (1. - forget) * new
  
  def train(self, history, actions, state, **unused):
    """Computes the model's loss on a given set of transitions.
    
    Args:
      history: List of game states from past to present, of length M+1. Each element is a tensor of shape [T-M, B, F].
        The states with valid histories are indexed [M, T).
      actions: Integer tensor of actions taken, of shape [T-M, B], corresponding to times [M, T).
      state: Raw, unembedded state structure of shape [T, B] tensors. Used for getting the first residual state.
    
    Returns:
      A tuple of (train_op, history). The history is extended by P steps into the future,
      and is now an M+P length list of shape [T-M-P, B, F] tensors. Valid time steps are [M+P, T)
    """
    memory = self.rlConfig.memory
    length = self.rlConfig.experience_length - memory - self.predict_steps

    history = [h[:-self.predict_steps] for h in history]
    current_actions = tfl.windowed(actions, self.predict_steps)
    
    states = util.deepMap(lambda t: tfl.windowed(t[memory:], self.predict_steps), state)
    begin_states = util.deepMap(lambda t: t[0], states)
    target_states = util.deepMap(lambda t: t[1:], states)
    
    last_states = self.embedGame(begin_states, residual=True)
    predicted_ta = tf.TensorArray(last_states.dtype, size=self.predict_steps, element_shape=last_states.get_shape())
    
    def predict_step(i, prev_history, prev_state, predicted_ta):
      current_action = current_actions[i]
      inputs = tf.concat(axis=2, values=prev_history + [current_action])
      
      predicted_state = self.apply(inputs, prev_state)
      
      next_inputs = self.embedGame.to_input(predicted_state)
      next_inputs = tf.concat(axis=2, values=[next_inputs, current_action])
      next_history = prev_history[1:] + [next_inputs]
    
      predicted_ta = predicted_ta.write(i, predicted_state)
      return i+1, next_history, predicted_state, predicted_ta
    
    loop_vars = (0, history, last_states, predicted_ta)
    cond = lambda i, *_: i < self.predict_steps
    _, history, _, predicted_ta = tf.while_loop(cond, predict_step, loop_vars)
    predicted_states = predicted_ta.stack()
    predicted_states.set_shape([self.predict_steps, length, None, self.embedGame.size])
    
    distances = self.embedGame.distance(predicted_states, target_states)
    distances = util.deepMap(lambda t: tf.reduce_mean(t, [1, 2]), distances)
    total_distances = tf.add_n(list(util.deepValues(distances)))
    for step in range(self.predict_steps):
      # log all the individual distances
      for path, tensor in util.deepItems(distances):
        tag = "model/%d/" % step + "/".join(map(str, path))
        tf.summary.scalar(tag, tensor[step])
    
      tf.summary.scalar("model/%d/total" % step, total_distances[step])
    
    total_distance = tf.reduce_sum(total_distances)
    self.opt = tf.train.AdamOptimizer(self.model_learning_rate)
    train_op = self.opt.minimize(total_distance, var_list=self.variables)
    return train_op, history
  
  def predict(self, history, actions, raw_state):
    last_state = util.deepMap(lambda t: t[-1], raw_state)
    last_state = self.embedGame(last_state, residual=True)

    def predict_step(i, prev_history, prev_state):
      current_action = actions[i]
      inputs = tf.concat(axis=-1, values=prev_history + [current_action])
      
      predicted_state = self.apply(inputs, prev_state)
      
      next_inputs = self.embedGame.to_input(predicted_state)
      next_inputs = tf.concat(axis=-1, values=[next_inputs, current_action])
      next_history = prev_history[1:] + [next_inputs]
    
      return i+1, next_history, predicted_state

    loop_vars = (0, history, last_state)
    cond = lambda i, *_: i < self.predict_steps
    _, predicted_history, _ = tf.while_loop(cond, predict_step, loop_vars)

    for step, action in enumerate(tf.unstack(actions)):
      input_ = tf.concat(axis=0, values=history[step:] + [action])
      predicted_state = self.apply(input_, last_state)
      
      # prepare for the next frame
      last_state = predicted_state
      next_input = self.embedGame.to_input(predicted_state)
      history.append(tf.concat(axis=0, values=[next_input, action]))
    
    difference = tf.abs(predicted_history[-1] - history[-1])
    same_difference = tf.assert_less(difference, 1e-5)
    
    with tf.control_dependencies([same_difference]):
      history[-1] = tf.identity(history[-1])
    
    return predicted_history
  
  def test_train_predict(self):
    dummy_input = tf.zeros([self.embedGame.size + self.action_size])
    history = [dummy_input] * (self.rlConfig.memory + 1)
    raw_state = [self.embedGame.extract(dummy_input)] * self.predict_steps
    actions = [tf.constant(0)] * self.predict_steps
    
    predictions = self.predict(history, actions, raw_state)
    
    
