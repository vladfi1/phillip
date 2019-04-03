import tensorflow as tf
import sonnet as snt

from ray import rllib
from ray.rllib.models.catalog import ModelCatalog

class DelayedActionModel(rllib.models.Model):

  def _build_layers_v2(self, input_dict, num_outputs, options):
    delay = options["custom_options"]["delay"]
    
    
    
    trunk = snt.nets.MLP(
        output_sizes=options["fcnet_hiddens"],
        activation=getattr(tf.nn, options["fcnet_activation"]),
        activate_final=True)

    trunk_outputs = trunk(input_dict["obs"])
    
    logits = snt.Linear(num_outputs)(trunk_outputs)
    
    return logits, trunk_outputs

def register():
  ModelCatalog.register_custom_model("delayed_action", DelayedActionModel)

