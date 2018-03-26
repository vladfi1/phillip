import tensorflow as tf
from . import tf_lib as tfl
from .default import *
import itertools

class Core(Default):
  _options = [
    Option('recurrent', type=int, default=0, help='Whether agent core is recurrent.'),
    Option('core_layers', type=int, nargs='+', default=[]),
  ]
  
  _members = [
    #('optimizer', opt.Optimizer),
    ('nl', tfl.NL),
  ]
  
  def __init__(self, input_size, scope='core', **kwargs):
    Default.__init__(self, **kwargs)
    
    with tf.variable_scope(scope):
      prev_size = input_size
      if self.recurrent:
        cells = []
        for i, next_size in enumerate(self.core_layers):
          with tf.variable_scope('layer_%d' % i):
            cells.append(tfl.GRUCell(prev_size, next_size))
          prev_size = next_size
        self.core = tf.nn.rnn_cell.MultiRNNCell(cells)
        self.hidden_size = self.core.state_size
        self.variables = list(itertools.chain.from_iterable([c.getVariables() for c in cells]))
      else:
        self.core = tfl.Sequential()
        for i, next_size in enumerate(self.core_layers):
          with tf.variable_scope("layer_%d" % i):
            self.core.append(tfl.FCLayer(prev_size, next_size, self.nl))
          prev_size = next_size
        self.hidden_size = []
        self.variables = self.core.getVariables()
      self.output_size = prev_size
 
  def __call__(self, inputs, state):
    if self.recurrent:
      return self.core(inputs, state)
    else:
      return self.core(inputs), []

