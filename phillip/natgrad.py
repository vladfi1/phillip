import tensorflow as tf
from .default import *
from . import tf_lib as tfl, cg

class NaturalGradient(Default):
  _options = [
    Option('target_distance', type=float, default=None, help="Target natural gradient distance."),
  ]
  
  _members = [
    ('cg', cg.ConjugateGradient),
  ]
  
  def __call__(self, params, direction, predictions, metric, **kwargs):
    """
    Corrects the given direction to account for the natural metric of the model space.
    
    Arguments:
      params: The parameters (tf Variables) that we are optimizing.
      direction: Initial direction in which we want to adjust the parameters.
      predictions: Function of the parameters (and data). This is the space in which we want to move.
      metric: Metric that defines the geometry of the function space.
    """
    param_shapes = [param.get_shape() for param in params]
    param_sizes = [shape.num_elements() for shape in param_shapes]
    param_offsets = []
    offset = 0
    for size in param_sizes:
      low = offset
      offset += size
      param_offsets.append((low, offset))
    
    def flatten(params_like):
      return tf.concat(0, [tf.reshape(x, [size]) for x, size in zip(params_like, param_sizes)])
    
    def unflatten(flat):
      slices = [flat[low:high] for low, high in param_offsets]
      return [tf.reshape(x, shape) for x, shape in zip(slices, param_shapes)]
    
    if isinstance(predictions, list):
      predictions_fixed = list(map(tf.stop_gradient, predictions))
    else: # assume we have a tensor
      predictions_fixed = tf.stop_gradient(predictions)
    distance = metric(predictions_fixed, predictions)
    
    distance_gradients = tf.gradients(distance, params)
    distance_gradients = flatten(distance_gradients)
    
    def fvp(tangent):
      with tf.name_scope('fvp'):
        tangent = tf.stop_gradient(tangent)
        gvp = tfl.dot(distance_gradients, tangent)
        fvp = tf.gradients(gvp, params)
        return flatten(fvp)
    
    direction_flat = flatten(direction)
    
    if self.cg.cg_iters:
      direction_natural = self.cg(fvp, direction_flat, **kwargs)
    else:
      direction_natural = direction_flat
    
    if self.target_distance is not None:
      projected_distance = .5 * tfl.dot(direction_natural, fvp(direction_natural))
      
      step_size = tf.sqrt(self.target_distance / projected_distance)
      #step_size = tf.minimum(1.0, step_size)
      tf.scalar_summary('ng_step', step_size)
      
      direction_natural *= step_size
      
      progress = tfl.dot(direction_natural, direction_flat)
      tf.scalar_summary('ng_progress', progress)
    
    return unflatten(direction_natural)

