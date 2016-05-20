import tensorflow as tf
#import pdb
import ctypes
import math
import functools
import operator

def leaky_relu(x, alpha=0.01):
  return tf.maximum(alpha * x, x)

def product(xs):
  return functools.reduce(operator.mul, xs, 1.0)

def batch_dot(xs, ys):
  return tf.reduce_sum(tf.mul(xs, ys), 1)

def weight_variable(shape):
    '''
    Generates a TensorFlow Tensor. This Tensor gets initialized with values sampled from the truncated normal
    distribution. Its purpose will be to store model parameters.
    :param shape: The dimensions of the desired Tensor
    :return: The initialized Tensor
    '''
    #initial = tf.truncated_normal(shape, stddev=0.1)
    input_size = product(shape[:-1])
    initial = tf.truncated_normal(shape, stddev=1.0/math.sqrt(input_size))
    return tf.Variable(initial)

def bias_variable(shape):
    '''
    Generates a TensorFlow Tensor. This Tensor gets initialized with values sampled from <some?> distribution.
    Its purpose will be to store bias values.
    :param shape: The dimensions of the desired Tensor
    :return: The initialized Tensor
    '''
    size = 1.0 / math.sqrt(product(shape))
    initial = tf.random_uniform(shape, -size, size)
    return tf.Variable(initial)

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

def affineLayer(x, output_size, nl=None):
  W = weight_variable([x.get_shape()[-1].value, output_size])
  b = bias_variable([output_size])

  fc = tf.matmul(x, W) + b

  return nl(fc) if nl else fc

def makeAffineLayer(input_size, output_size, nl=None):
  W = weight_variable([input_size, output_size])
  b = bias_variable([output_size])

  def applyLayer(x):
    fc = tf.matmul(x, W) + b

    return nl(fc) if nl else fc

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
