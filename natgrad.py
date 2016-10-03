import tensorflow as tf

def dot(x, y):
  return tf.reduce_sum(x * y)

def mag2(x):
  return tf.reduce_sum(tf.square(x))

def natural_gradients(params, direction, predictions, metric, target_distance=None, **kwargs):
  """
  Corrects the given direction to account for the natural metric of the model space.
  
  Arguments:
    params: The parameteries (tf Variables) that we are optimizing.
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
      gvp = tf.reduce_sum(distance_gradients * tangent)
      fvp = tf.gradients(gvp, params)
      return flatten(fvp)
  
  direction_flat = flatten(direction)
  
  direction_natural = cg(fvp, direction_flat, **kwargs)
  
  if target_distance:
    acceleration = .5 * dot(direction_natural, direction)
    #acceleration = .5 * dot(direction_natural, fvp(direction_natural))
    
    step_size = tf.sqrt(acceleration / target_distance)
    step_size = tf.minimum(1.0, step_size)
    
    direction_natural *= step_size
  
  return unflatten(direction_natural)

def cg(f_Ax, b, cg_iters=10, residual_tol=1e-10, cg_damping=1e-4, debug=False, **kwargs):
  """
  Conjugate gradient descent. Finds the solution to Ax = b. The matrix A is represented
  indirectly by a callable that performs multiplication by an arbitrary vector.
  
  Arguments:
    f_Ax: Callable that, given a 1D tensor x, returns Ax.
    b: The 1D target for Ax.
    iters: Maximum number of conjugate gradient steps.
    residual_tol: Stops cg iteration if the residual (squared) magnitude falls below this value.
    damping: Adds a multiple of the identity matrix to A.
    debug: Whether to return all the cg loop variables.
  
  Returns:
    The solution to the system Ax = b.
    If debug is True, then we return the tuple (n, x, p, r, rr).
  
  Source: Demmel p 312, adapted from OpenAI's numpy implementation.
  """
  
  def body(n, x, p, r, rr):
    z = f_Ax(p) + cg_damping * p
    v = rr / dot(p, z)
    x += v*p
    r -= v*z
    new_rr = mag2(r)
    mu = new_rr / rr
    p = r + mu * p

    rr = new_rr
    
    n += 1
    
    return (n, x, p, r, rr)
  
  def cond(n, x, p, r, rr):
    return tf.logical_and(tf.less(n, cg_iters), tf.less(residual_tol, rr))
  
  with tf.name_scope('cg'):
    n = tf.constant(0)
    p = b
    r = b
    x = tf.zeros_like(b)
    rr = mag2(r)
    
    n, x, p, r, rr = tf.while_loop(cond, body, (n, x, p, r, rr), back_prop=False)
    
    if debug:
      return n, x, p, r, rr
    else:
      return x

def test_cg():
  sess = tf.Session()

  with sess.graph.as_default():
    A = tf.constant([[2, 1], [1, 5]], dtype=tf.float32)
    b = tf.constant([-4, 7], dtype=tf.float32)
    
    f = lambda x: tf.reduce_sum(A * x, 1)
    cg_output = cg(f, b, damping=0, debug = True)
  
  results = sess.run(cg_output)
  
  print(*results)
  
  import numpy as np
  expected = np.array([-3, 2])
  x = results[1]
  assert(np.linalg.norm(x - expected) < 1e-6)

