import tensorflow as tf
from . import tf_lib as tfl
from .default import *
import itertools

class Core(Default):
  _options = [
    Option('trunk_layers', type=int, nargs='+', default=[], help="Non-recurrent layers."),
    Option('core_layers', type=int, nargs='+', default=[], help="Recurrent layers."),
  ]
  
  _members = [
    #('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, input_size, scope='core', **kwargs):
    Default.__init__(self, **kwargs)
    
    with tf.variable_scope(scope):
      prev_size = input_size
      
      with tf.variable_scope("trunk"):
        self.trunk = tfl.Sequential()
        for i, next_size in enumerate(self.trunk_layers):
          with tf.variable_scope("layer_%d" % i):
            self.trunk.append(tfl.FCLayer(prev_size, next_size, self.nl))
          prev_size = next_size
        self.variables = self.trunk.getVariables()
  
      if self.core_layers:
        cells = []
        for i, next_size in enumerate(self.core_layers):
          with tf.variable_scope('layer_%d' % i):
            cell = tfl.GRUCell(prev_size, next_size)
            cells.append(cell)
            self.variables += cell.getVariables()
          prev_size = next_size
        self.core = tf.nn.rnn_cell.MultiRNNCell(cells)
        self.hidden_size = self.core.state_size
      else:
        self.core = None
        self.hidden_size = []
      self.output_size = prev_size
 
  def __call__(self, inputs, state):
    trunk_outputs = self.trunk(inputs)
    if self.core:
      return self.core(trunk_outputs, state)
    else:
      return trunk_outputs, []

