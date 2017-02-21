import tensorflow as tf
from . import tf_lib as tfl
from .default import *

def mag2(x):
  return tf.reduce_sum(tf.square(x))

class ConjugateGradient(Default):
  _options = [
    Option('cg_iters', type=int, default=10, help="Maximum number of conjugate gradient iterations."),
    Option('residual_tol', type=float, default=1e-10, help="Minimum conjugate gradient residual tolerance."),
    Option('cg_damping', type=float, default=1e-4, help="Add a multiple of the identity function during conjugate gradient descent."),
  ]
  
  def __call__(self, f_Ax, b, debug=False):
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
      z = f_Ax(p) + self.cg_damping * p
      v = rr / tfl.dot(p, z)
      x += v*p
      r -= v*z
      new_rr = mag2(r)
      mu = new_rr / rr
      p = r + mu * p

      rr = new_rr
      
      n += 1
      
      return (n, x, p, r, rr)
    
    def cond(n, x, p, r, rr):
      return tf.logical_and(tf.less(n, self.cg_iters), tf.less(self.residual_tol, rr))
    
    with tf.name_scope('cg'):
      n = tf.constant(0)
      x = tf.zeros_like(b)
      r = b
      #x = b # this way cg_iters = 0 means we use the original direction
      #r = b - f_Ax(x)
      p = r
      rr = mag2(r)
      
      n, x, p, r, rr = tf.while_loop(cond, body, (n, x, p, r, rr), back_prop=False)
      
      tf.scalar_summary('cg_iters', n)
      tf.scalar_summary('cg_error', tf.sqrt(rr / mag2(b)))
      tf.scalar_summary('cg_loss', -0.5 * tfl.dot(x, b+r))
      
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
    
    cg = ConjugateGradient(cg_damping=0)
    cg_output = cg(f, b, debug = True)
  
  results = sess.run(cg_output)
  
  print(*results)
  
  import numpy as np
  expected = np.array([-3, 2])
  x = results[1]
  assert(np.linalg.norm(x - expected) < 1e-6)

