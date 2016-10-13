from dqn import DQN
import natgrad
import tf_lib as tfl
import tensorflow as tf

class NaturalDQN(DQN):
  _members = [
    ('natgrad', natgrad.NaturalGradient)
  ]
  
  def train(self, *args):
    DQN.train(self, *args)
    
    def q_metric(q1, q2):
      return self.action_size * tf.reduce_mean(tf.squared_difference(q1, q2))
      
    ng = self.natgrad(self.params, self.gradients, self.predictedQs, q_metric)
    
    return tfl.apply_grads(self.params, ng)
