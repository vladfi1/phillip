import numpy as np
import tensorflow as tf
from tensorflow.contrib.framework.python.framework import checkpoint_utils
import itertools
from phillip.default import *
from phillip import util

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
  return tf.reduce_sum(tf.multiply(xs, ys), -1)

def dot(x, y):
  return tf.reduce_sum(x * y)

def power(x, p):
  if p == 1:
    return x
  if p == -1:
    return tf.reciprocal(x)
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

def stats(xs, name=None, minmax=False):
  mean = tf.reduce_mean(xs)
  std = tf.sqrt(tf.reduce_mean(tf.squared_difference(xs, mean)))
  
  if name:
    tf.summary.scalar(name + '/mean', mean)
    tf.summary.scalar(name + '/std', std)
    if minmax:
      tf.summary.scalar(name + '/min', tf.reduce_min(xs))
      tf.summary.scalar(name + '/max', tf.reduce_max(xs))

  return mean, std

def apply_grads(params, grads):
  return tf.group(*[tf.assign_add(p, g) for p, g in zip(params, grads)])

def scale_gradient(t, scale):
  return (1.-scale) * tf.stop_gradient(t) + scale * t

def windowed(t, n):
  """Gives a windowed view into a Tensor.
  
  Args:
    t: The input Tensor with shape [T, ...]
    n: An integer >= 0.
  Returns:
    A Tensor with shape [n+1, T-n, ...]
  """
  return tf.stack([t[i:i-n] for i in range(n)] + [t[n:]])

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

def weight_init(shape):
    initial = tf.random_normal(shape, stddev=1.0)
    
    norms = tf.sqrt(tf.reduce_sum(tf.square(initial), list(range(len(shape)-1))))
    initial /= norms
    
    return initial

def weight_variable(shape, name="weight"):
    return tf.Variable(weight_init(shape), name=name)

def bias_init(shape):
    return tf.truncated_normal(shape, stddev=0.1)

def bias_variable(shape, name="bias"):
    return tf.Variable(bias_init(shape), name=name)

def constant_init(c):
    return lambda shape: tf.constant(c, shape=shape)

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
  v = tf.expand_dims(v, -1)
  vm = tf.multiply(v, m)
  return tf.reduce_sum(vm, -2)

# I think this is the more efficient version?
def matmul2(x, m, bias=None, nl=None):
  [input_size, output_size] = m.get_shape().as_list()
  input_shape_py = x.get_shape().as_list()
  assert(input_shape_py[-1] == input_size)
  
  input_shape_tf = tf.shape(x)
  batch_rank = len(input_shape_py) - 1
  batch_shape_tf = input_shape_tf[:batch_rank]
  output_shape_tf = tf.concat(axis=0, values=[batch_shape_tf, [output_size]])
  
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

class FCLayer(Default):
  _options = [
    Option("weight_init", default=weight_init),
    Option("bias_init", default=bias_init),
  ]
  
  def __init__(self, input_size=None, output_size=None, nl=None, clone=None, **kwargs):
    if clone:
      self.input_size = clone.input_size
      self.output_size = clone.output_size
      self.nl = clone.nl
      
      self.weight = cloneVar(clone.weight)
      self.bias = cloneVar(clone.bias)
    else:
      Default.__init__(self, **kwargs)
      
      self.input_size = input_size
      self.output_size = output_size
      self.nl = nl
      
      self.weight = tf.Variable(self.weight_init([input_size, output_size]), name="weight")
      self.bias = tf.Variable(self.bias_init([output_size]), name="bias")
  
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

class GRUCell(tf.contrib.rnn.RNNCell):
  def __init__(self, input_size, hidden_size, nl=tf.tanh, name=None):
    with tf.variable_scope(name or type(self).__name__):
      with tf.variable_scope("Gates"):
        self.Wru = weight_variable([input_size + hidden_size, 2 * hidden_size])
        self.bru = tf.Variable(tf.constant(1.0, shape=[2 * hidden_size]), name='bias')
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
    ru = tf.sigmoid(matmul2(tf.concat(axis=-1, values=[inputs, state]), self.Wru) + self.bru)
    r, u = tf.split(axis=-1, num_or_size_splits=2, value=ru)
    
    c = self.nl(matmul2(tf.concat(axis=-1, values=[inputs, r * state]), self.Wc) + self.bc)
    new_h = u * state + (1 - u) * c
    
    return new_h, new_h
  
  def getVariables(self):
    return [self.Wru, self.bru, self.Wc, self.bc]

# auto unpacks and repacks inputs
def rnn(cell, inputs, initial_state, time=1):
  inputs = tf.unstack(inputs, axis=time)
  outputs = []
  state = initial_state
  for i, input_ in enumerate(inputs):
    output, state = cell(input_, state)
    outputs.append(output)
  return tf.stack(outputs, axis=time), state

def scan(f, inputs, initial_state, axis=0):
  inputs = util.deepIter(util.deepMap(lambda t: iter(tf.unstack(t, axis=axis)), inputs))
  outputs = []
  output = initial_state
  for input_ in inputs:
    output = f(output, input_)
    outputs.append(output)
  return util.deepZipWith(lambda *ts: tf.stack(ts, axis=axis), *outputs)

def while_loop(cond, body, initial):
  while cond(*initial):
    initial = body(*initial)
  return initial

class TensorArray(object):
  def __init__(self, dtype, size, element_shape):
    self.elems = [None] * size
  
  def write(self, i, t):
    self.elems[i] = t
    return self
  
  def stack(self):
    return tf.stack(self.elems)

def discount(values, gamma, initial=None):
  values = tf.unstack(values, axis=1)
  
  if initial is None:
    current = tf.zeros_like(values[0])
  else:
    current = initial
  
  for i in reversed(range(len(values))):
    current = values[i] + gamma * current
    values[i] = current
  
  return tf.stack(values, axis=1)

def discount2(values, gamma, initial=None):
  """Compute returns from rewards.
  
  Uses tf.while_loop instead of unrolling in python.
  
  Arguments:
    values: Tensor with shape [time, batch]
    gamma: Discount factor.
    initial: Value past the end.
  
  Returns:
    A tensor of discounted returns.
  """
  
  def body(i, prev, returns):
    next = values[i] + gamma * prev
    next.set_shape(prev.get_shape())
    
    returns = returns.write(i, next)

    return (i-1, next, returns)

  def cond(i, prev, returns):
    return i >= 0
  
  if initial is None:
    initial = tf.zeros(tf.shape(values)[1:], values.dtype)

  timesteps = tf.shape(values)[0]

  ta = tf.TensorArray(values.dtype, timesteps)
  
  _, _, returns = tf.while_loop(cond, body, (timesteps-1, initial, ta))
  
  return returns.stack()

def testDiscounts():
  values = tf.constant([[1, 2, 3]])
  gamma = 2
  initial = tf.constant([4])
  
  correct = [[49, 24, 11]]
  
  fs = [discount, discount2]
  
  fetches = [f(values, gamma, initial) for f in fs]

  sess = tf.Session()
  returns = sess.run(fetches)
  
  for r in returns:
    assert((r == correct).all())

  print("Passed testDiscount()")

def smoothed_returns(values, rewards, gamma, lambda_, bootstrap, dynamic=True):
  def bellman(future, present):
    v, r, l = present
    return (1. - l) * v + l * (r + gamma * future)
  
  reversed_sequence = [tf.reverse(t, [0]) for t in [values, rewards, lambda_]]
  scan_fn = tf.scan if dynamic else scan
  returns = scan_fn(bellman, reversed_sequence, bootstrap)
  returns = tf.reverse(returns, [0])
  return returns

def test_smoothed_returns():
  values = tf.zeros([3, 1])
  rewards = tf.constant([[1.], [2.], [3.]])
  gamma = 2
  lambda_ = tf.ones([3, 1])
  initial = tf.constant([4.])
  
  correct = [[49], [24], [11]]
  
  fs = [smoothed_returns]
  
  fetches = [f(values, rewards, gamma, lambda_, initial) for f in fs]

  sess = tf.Session()
  returns = sess.run(fetches)
  
  for r in returns:
    assert((r == correct).all())

  print("Passed test_smoothed_returns()")

def restore(session, variables, ckpt_path):
  """Does what a saver would do, but handles mismatched shapes."""
  ckpt = checkpoint_utils.load_checkpoint(ckpt_path)

  for var in variables:
    name = var.name
    if name.endswith(":0"):
      name = name[:-2]
    if not ckpt.has_tensor(name):
      print("%s not in checkpoint, initializing" % name)
      var.load(session.run(var.initial_value), session)
      continue
    value = ckpt.get_tensor(name)
    pads = [(0, d1 - d2) for d1, d2 in zip(var.get_shape().as_list(), value.shape)]
    needs_pad = any([p[1] for p in pads])
    if needs_pad:
      print("Variable %s of shape %s padded from %s" % (var.name, var.get_shape().as_list(), value.shape))
      value = np.pad(value, pads, "constant")
    var.load(value, session)
