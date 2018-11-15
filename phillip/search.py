import tensorflow as tf
from . import tf_lib as tfl
from .default import Default, Option

nest = tf.contrib.framework.nest

class SearchPolicy(Default):

  _options = [
    Option("search_temp", type=float),
    Option("beam_width", type=int, default=50),
  ]
  
  def __init__(self, model, embedAction, critic, **kwargs):
    Default.__init__(self, **kwargs)
    self.model = model
    self.embedAction = embedAction
    self.critic = critic
  
  def children(self, batch_size, parent_inputs):
    # FIXME: only works for OneHotEmbedding
    all_actions = tf.eye(self.embedAction.size)
    all_actions = tfl.tile(all_actions, batch_size, 0)
    
    f = lambda t: tfl.tile(t, self.embedAction.size, 1)
    parent_inputs = nest.map_structure(f, parent_inputs)
    
    return self.model.predict_step(parent_inputs, all_actions)
  
  def get_policy(self, model_input):
    children = self.children(1, model_input)
    child_values = self.critic(children.core_output)
    
    if self.search_temp:
      return tf.nn.softmax(child_values / self.search_temp)
    else:
      return tf.contrib.seq2seq.hardmax(child_values)

