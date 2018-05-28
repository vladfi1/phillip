from phillip import RL
import tensorflow as tf
from . import ssbm, util, ctype_util as ct, embed
from .core import Core
from .ac import ActorCritic

class Actor(RL.RL):
  def __init__(self, **kwargs):
    super(Actor, self).__init__(**kwargs)

    with self.graph.as_default(), tf.device(self.device): 
      if self.predict: self._init_model(**kwargs)
      self._init_policy(**kwargs)
      
      # build computation graph
      self.input = ct.inputCType(ssbm.SimpleStateAction, [self.config.memory+1], "input")
      self.input['delayed_action'] = tf.placeholder(tf.int64, [self.config.delay], "delayed_action")
      self.input['hidden'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [size], name="input/hidden"), self.core.hidden_size)

      states = self.embedGame(self.input['state'])
      prev_actions = self.embedAction(self.input['prev_action'])
      combined = tf.concat(axis=-1, values=[states, prev_actions])
      history = tf.unstack(combined)
      inputs = tf.concat(axis=-1, values=history)
      core_output, hidden_state = self.core(inputs, self.input['hidden'])
      actions = self.embedAction(self.input['delayed_action'])
      
      if self.predict:
        predict_actions = actions[:self.model.predict_steps]
        delayed_actions = actions[self.model.predict_steps:]
        core_output = self.model.predict(history, core_output, hidden_state, predict_actions, self.input['state'])
      else:
        delayed_actions = actions
      
      self.run_policy = self.policy.getPolicy(core_output, delayed_actions), hidden_state
      
      self._finalize_setup()

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    policy, hidden = self.sess.run(self.run_policy, feed_dict)
    return self.policy.act(policy, verbose), hidden
