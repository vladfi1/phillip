import tensorflow as tf
#import pdb
import ctypes
import math
import itertools
#import util
from .default import *

def leaky_relu(x, alpha=0.01):
  return tf.maximum(alpha * x, x)

def log_sum_exp(xs):
  maxes = tf.reduce_max(xs, -1, keep_dims=True)
  maxes = tf.stop_gradient(maxes)
  return tf.squeeze(maxes, [-1]) + tf.log(tf.reduce_sum(tf.exp(xs-maxes), -1))

def leaky_softplus(x, alpha=0.01):
  "Really just a special case of log_sum_exp."
  ax = alpha * x
  maxes = tf.stop_gradient(tf.maximum(ax, x))
  return maxes + tf.log(tf.exp(ax - maxes) + tf.exp(x - maxes))

class NL(Default):
  _options = [
    Option('nl', type=str, choices=['leaky_relu', 'leaky_softplus', 'elu', 'relu', 'tanh', 'sigmoid'], default='leaky_softplus'),
    Option('alpha', type=float, default=0.01),
  ]
  
  def __call__(self, x):
    if self.nl == 'leaky_relu':
      return leaky_relu(x, self.alpha)
    elif self.nl == 'leaky_softplus':
      return leaky_softplus(x, self.alpha)
    else:
      return getattr(tf.nn, self.nl)(x)

def batch_dot(xs, ys):
  return tf.reduce_sum(tf.mul(xs, ys), -1)

def dot(x, y):
  return tf.reduce_sum(x * y)

def power(x, p):
  if p == 1:
    return x
  if p == -1:
    return tf.inv(x)
  return tf.pow(x, p)

def geometric_mean(xs):
  return tf.exp(tf.reduce_mean(tf.log(xs)))

def power_mean(p, xs):
  if p == 0:
    return geometric_mean(xs)
  return power(tf.reduce_mean(power(xs, p)), 1/p)

def sym_kl(logp, logq):
  return 0.5 * batch_dot(tf.exp(logp) - tf.exp(logq), logp - logq)

def kl(logp, logq):
  return batch_dot(tf.exp(logp), logp - logq)

def sample_variance(xs):
  return tf.reduce_mean(tf.squared_difference(xs, tf.reduce_mean(xs)))

def apply_grads(params, grads):
  return tf.group(*[tf.assign_add(p, g) for p, g in zip(params, grads)])

def scaled_weight_variable(shape):
    '''
    Generates a TensorFlow Tensor. This Tensor gets initialized with values sampled from the truncated normal
    distribution. Its purpose will be to store model parameters.
    :param shape: The dimensions of the desired Tensor
    :return: The initialized Tensor
    '''
    #input_size = util.product(shape[:-1])
    w = tf.Variable(tf.truncated_normal(shape, stddev=1.0), name='weight')
    
    norms = tf.sqrt(tf.reduce_sum(tf.square(w), list(range(len(shape)-1))))
    w /= norms
    
    scale = tf.Variable(tf.truncated_normal(shape[-1:], stddev=1.0), name='scale')
    
    return scale * w
    
def weight_variable(shape):
    initial = tf.random_normal(shape, stddev=1.0)
    
    norms = tf.sqrt(tf.reduce_sum(tf.square(initial), list(range(len(shape)-1))))
    initial /= norms
    
    return tf.Variable(initial, name='weight')

def bias_variable(shape):
    '''
    Generates a TensorFlow Tensor. This Tensor gets initialized with values sampled from <some?> distribution.
    Its purpose will be to store bias values.
    :param shape: The dimensions of the desired Tensor
    :return: The initialized Tensor
    '''
    return tf.Variable(tf.truncated_normal(shape, stddev=0.1), name='bias')

def conv2d(x, W):
    '''
    Generates a conv2d TensorFlow Op. This Op flattens the weight matrix (filter) down to 2D, then "strides" across the
    input Tensor x, selecting windows/patches. For each little_patch, the Op performs a right multiply:
            W . little_patch
    and stores the result in the output layer of feature maps.
    :param x: a minibatch of images with dimensions [batch_size, height, width, 3]
    :param W: a "filter" with dimensions [window_height, window_width, input_channels, output_channels]
    e.g. for the first conv layer:
          input_channels = 3 (RGB)
          output_channels = number_of_desired_feature_maps
    :return: A TensorFlow Op that convolves the input x with the filter W.
    '''
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

def max_pool_2x2(x):
    '''
    Genarates a max-pool TensorFlow Op. This Op "strides" a window across the input x. In each window, the maximum value
    is selected and chosen to represent that region in the output Tensor. Hence the size/dimensionality of the problem
    is reduced.
    :param x: A Tensor with dimensions [batch_size, height, width, 3]
    :return: A TensorFlow Op that max-pools the input Tensor, x.
    '''
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1], padding='SAME')

def convLayer(x, filter_size=5, filter_depth=64, pool_size=2):
  x_depth = x.get_shape()[-1].value
  W = weight_variable([filter_size, filter_size, x_depth, filter_depth])
  conv = tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

  b = bias_variable([filter_depth])
  relu = tf.nn.relu(conv + b)

  pool = tf.nn.max_pool(relu,
                        ksize=[1,pool_size,pool_size,1],
                        strides=[1,pool_size,pool_size,1],
                        padding = 'SAME')

  return pool

def softmax(x):
  input_shape = tf.shape(x)
  input_rank = tf.shape(input_shape)[0]
  input_size = tf.gather(input_shape, input_rank-1)
  output_shape = input_shape
  
  x = tf.reshape(x, [-1, input_size])

  y = tf.nn.softmax(x)
  y = tf.reshape(y, output_shape)
  
  return y

def matmul(v, m):
  shape = tf.shape(v)
  rank = shape.get_shape()[0].value
  v = tf.expand_dims(v, rank)
  
  vm = tf.mul(v, m)
  
  return tf.reduce_sum(vm, rank-1)

# I think this is the more efficient version?
def matmul2(x, m, bias=None, nl=None):
  [input_size, output_size] = m.get_shape().as_list()
  input_shape_py = x.get_shape().as_list()
  assert(input_shape_py[-1] == input_size)
  
  input_shape_tf = tf.shape(x)
  batch_rank = len(input_shape_py) - 1
  batch_shape_tf = input_shape_tf[:batch_rank]
  output_shape_tf = tf.concat(0, [batch_shape_tf, [output_size]])
  
  squashed = tf.reshape(x, [-1, input_size])
  y = tf.matmul(squashed, m)
  
  if bias is not None:
    y += bias
  
  if nl is not None:
    y = nl(y)
  
  y = tf.reshape(y, output_shape_tf)
  
  # fix shape inference
  output_shape_py = input_shape_py.copy()
  output_shape_py[-1] = output_size
  y.set_shape(output_shape_py)
  
  return y

def cloneVar(var):
  return tf.Variable(var.initialized_value())

class FCLayer:
  def __init__(self, input_size=None, output_size=None, nl=None, clone=None):
    if clone:
      self.input_size = clone.input_size
      self.output_size = clone.output_size
      self.nl = clone.nl
      
      self.weight = cloneVar(clone.weight)
      self.bias = cloneVar(clone.bias)
    else:
      self.input_size = input_size
      self.output_size = output_size
      self.nl = nl
      
      self.weight = weight_variable([input_size, output_size])
      self.bias = bias_variable([output_size])
  
  def __call__(self, x):
    return matmul2(x, self.weight, self.bias, self.nl)
    
  def clone(self):
    return FCLayer(clone=self)
  
  def assign(self, other):
    return [
      self.weight.assign(other.weight),
      self.bias.assign(other.bias),
    ]
  
  def getVariables(self):
    return [self.weight, self.bias]

class Sequential:
  def __init__(self, *layers):
    self.layers = list(layers)
  
  def append(self, layer):
    self.layers.append(layer)
  
  def __call__(self, x):
    for f in self.layers:
      x = f(x)
    return x
  
  def clone(self):
    layers = [layer.clone() for layer in self.layers]
    return Sequential(*layers)
  
  def assign(self, other):
    assignments = [l1.assign(l2) for l1, l2 in zip(self.layers, other.layers)]
    return list(itertools.chain(*assignments))

  def getVariables(self):
    variables = [layer.getVariables() for layer in self.layers]
    return list(itertools.chain(*variables))

def affineLayer(x, output_size, nl=None):
  W = weight_variable([x.get_shape()[-1].value, output_size])
  b = bias_variable([output_size])

  fc = matmul2(x, W) + b

  return nl(fc) if nl else fc

def makeAffineLayer(input_size, output_size, nl=None):
  W = weight_variable([input_size, output_size])
  b = bias_variable([output_size])

  def applyLayer(x):
    return matmul2(x, W, b, nl)

  return applyLayer

def clamp(x, minimum, maximum):
  return tf.minimum(tf.maximum(x, minimum), maximum)

def one_hot(size):
  """
  A clamped integer to one-hot vector function.
  """
  return lambda t: tf.one_hot(
      clamp(tf.cast(t, tf.int64), 0, size - 1),
      size,
      1.0,
      0.0)

def rank(t):
  return tf.shape(tf.shape(t))[0]

def run(session, fetches, feed_dict):
    """Wrapper for making Session.run() more user friendly.

    With this function, fetches can be either a list or a dictionary.

    If fetches is a list, this function will behave like
    tf.session.run() and return a list in the same order as well. If
    fetches is a dict then this function will also return a dict where
    the returned values are associated with the corresponding keys from
    the fetches dict.

    Keyword arguments:
    session -- An open TensorFlow session.
    fetches -- A list or dict of ops to fetch.
    feed_dict -- The dict of values to feed to the computation graph.
    """
    if isinstance(fetches, dict):
        keys, values = fetches.keys(), list(fetches.values())
        res = session.run(values, feed_dict)
        return {key: value for key, value in zip(keys, res)}
    else:
        return session.run(fetches, feed_dict)

class GRUCell(tf.nn.rnn_cell.RNNCell):
  def __init__(self, input_size, hidden_size, nl=tf.tanh, name=None):
    with tf.variable_scope(name or type(self).__name__):
      with tf.variable_scope("Gates"):
        self.Wru = weight_variable([input_size + hidden_size, 2 * hidden_size])
        self.bru = tf.Variable(tf.constant(1.0, shape=[2 * hidden_size]))
      with tf.variable_scope("Candidate"):
        self.Wc = weight_variable([input_size + hidden_size, hidden_size])
        self.bc = bias_variable([hidden_size])
    self.nl = nl
    self._num_units = hidden_size

  @property
  def state_size(self):
    return self._num_units

  @property
  def output_size(self):
    return self._num_units  
  
  def __call__(self, inputs, state):
    ru = tf.sigmoid(tf.matmul(tf.concat(1, [inputs, state]), self.Wru) + self.bru)
    r, u = tf.split(1, 2, ru)
    
    c = self.nl(tf.matmul(tf.concat(1, [inputs, r * state]), self.Wc) + self.bc)
    new_h = u * state + (1 - u) * c
    
    return new_h, new_h

# TODO: auto unpack and repack inputs?
def rnn(cell, inputs, initial_state, scope=None):
  outputs = []
  state = initial_state
  for i, input_ in enumerate(inputs):
    output, state = cell(input_, state)
    outputs.append(output)
  return outputs, state
