import tensorflow as tf
#import pdb
import ctypes

def shapeSize(shape):
  size = 1
  for dim in shape:
    size *= dim
  return size

def weight_variable(shape):
    '''
    Generates a TensorFlow Tensor. This Tensor gets initialized with values sampled from the truncated normal
    distribution. Its purpose will be to store model parameters.
    :param shape: The dimensions of the desired Tensor
    :return: The initialized Tensor
    '''
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    '''
    Generates a TensorFlow Tensor. This Tensor gets initialized with values sampled from <some?> distribution.
    Its purpose will be to store bias values.
    :param shape: The dimensions of the desired Tensor
    :return: The initialized Tensor
    '''
    initial = tf.constant(0.1, shape=shape)
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

# TODO: fill out the rest of this table
ctypes2TF = {
  ctypes.c_bool : tf.bool,
  ctypes.c_float : tf.float32,
  ctypes.c_double : tf.float64,
  ctypes.c_uint : tf.int32,
}

def inputCType(ctype, shape=None, name=""):
  if ctype in ctypes2TF:
    return tf.placeholder(ctypes2TF[ctype], shape, name)
  elif issubclass(ctype, ctypes.Structure):
    return {f : inputCType(t, shape, name + "/" + f) for (f, t) in ctype._fields_}
  else: # assume an array type
    base_type = ctype._type_
    return [inputCType(base_type, shape, name + "/" + str(i)) for i in range(ctype._length_)]

def feedCType(ctype, name, value, feed_dict=None):
  if feed_dict is None:
    feed_dict = {}
  if ctype in ctypes2TF:
    feed_dict[name + ':0'] = value
  elif issubclass(ctype, ctypes.Structure):
    for f, t in ctype._fields_:
      feedCType(t, name + '/' + f, getattr(value, f), feed_dict)
  else: # assume an array type
    base_type = ctype._type_
    for i in range(ctype._length_):
      feedCType(base_type, name + '/' + str(i), value[i], feed_dict)
  
  return feed_dict

def feedCTypes(ctype, name, values, feed_dict=None):
  if feed_dict is None:
    feed_dict = {}
  if ctype in ctypes2TF:
    feed_dict[name + ':0'] = values
  elif issubclass(ctype, ctypes.Structure):
    for f, t in ctype._fields_:
      feedCTypes(t, name + '/' + f, [getattr(v, f) for v in values], feed_dict)
  else: # assume an array type
    base_type = ctype._type_
    for i in range(ctype._length_):
      feedCTypes(base_type, name + '/' + str(i), [v[i] for v in values], feed_dict)
  
  return feed_dict

