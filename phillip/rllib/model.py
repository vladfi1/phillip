import numpy as np
import tensorflow as tf
import sonnet as snt

from ray import rllib
from ray.rllib.models.catalog import ModelCatalog

class DelayedActionModel(rllib.models.Model):

  def _build_layers_v2(self, input_dict, num_outputs, options):
    delay = options["custom_options"]["delay"]
    assert(delay > 0)
    
    self.state_init = np.zeros([delay-1], np.int64)

    if not self.state_in:
        self.state_in = tf.placeholder(tf.int64, [None, delay-1], name="delayed_actions")

    delayed_actions = tf.concat([
        self.state_in,
        tf.expand_dims(input_dict["prev_actions"], 1)
    ], axis=1)
    
    self.state_out = delayed_actions[:, 1:]
    
    embedded_delayed_actions = tf.one_hot(delayed_actions, num_outputs)
    embedded_delayed_actions = snt.MergeDims(1, 2)(embedded_delayed_actions)

    trunk = snt.nets.MLP(
        output_sizes=options["fcnet_hiddens"],
        activation=getattr(tf.nn, options["fcnet_activation"]),
        activate_final=True)

    inputs = tf.concat([input_dict["obs"], embedded_delayed_actions], 1)
    trunk_outputs = trunk(input_dict["obs"])
    
    logits = snt.Linear(num_outputs)(trunk_outputs)
    
    return logits, trunk_outputs

def register():
  ModelCatalog.register_custom_model("delayed_action", DelayedActionModel)

