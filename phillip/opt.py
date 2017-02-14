import tensorflow as tf

from .default import *
from . import natgrad

class Optimizer(Default):
  _options = [
    Option('learning_rate', type=float, default=0.001),
    Option('optimizer', type=str, default="GradientDescent", help="which tf.train optimizer to use"),
    Option('natural', action="store_true", help="Use natural gradient."),
    Option('clip', type=float, help="clip gradients above a certain value")
  ]
  
  _members = [
    ('natgrad', natgrad.NaturalGradient)
  ]
    
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.optimizer = getattr(tf.train, self.optimizer + 'Optimizer')(self.learning_rate)
  
  def optimize(self, loss, params=None, predictions=None, metric=None):
    grads_vars = self.optimizer.compute_gradients(loss, var_list=params)
    
    grads, params = map(list, zip(*grads_vars))
    
    if self.natural:
      grads = self.natgrad(params, grads, predictions, metric)
    
    grads = [tf.check_numerics(g, "NaN gradient in param %d" % i) for i, g in enumerate(grads)]
    
    flat_params, flat_grads = [tf.abs(tf.concat(0, [tf.reshape(t, [-1]) for t in ts])) for ts in (params, grads)]
    
    #flat_ratios = flat_grads / flat_params
    #tf.scalar_summary('grad_param_max', tf.reduce_max(flat_ratios))
    #tf.scalar_summary('grad_param_avg', tf.reduce_mean(flat_ratios))
    
    grad_max = tf.reduce_max(flat_grads)
    
    tf.scalar_summary('grad_max', grad_max)
    tf.scalar_summary('grad_avg', tf.reduce_mean(flat_grads))
    
    if self.clip:
      clip = tf.minimum(self.clip, grad_max) / grad_max
      grads = [g*clip for g in grads]
    
    return self.optimizer.apply_gradients(zip(grads, params))
