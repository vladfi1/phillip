import tensorflow as tf

from default import *
import natgrad

class Optimizer(Default):
  _options = [
    Option('learning_rate', type=float, default=0.001),
    Option('optimizer', type=str, default="GradientDescent", help="which tf.train optimizer to use"),
    Option('natural', action="store_true", help="Use natural gradient."),
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
    
    return self.optimizer.apply_gradients(zip(grads, params))
