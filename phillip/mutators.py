import tensorflow as tf
import random

def relative(factor):
  inverse = 1. / factor
  def mutate(x):
    flip = tf.distributions.Bernoulli(.5).sample()
    return x * tf.where(tf.cast(flip, tf.bool), factor, inverse)
  return mutate

