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

      batch_input = util.deepMap(lambda t: tf.expand_dims(t, 0), self.input)

      states = self.embedGame(batch_input['state'])
      prev_actions = self.embedAction(batch_input['prev_action'])
      combined = tf.concat(axis=-1, values=[states, prev_actions])
      history = tf.unstack(combined, axis=1)
      inputs = tf.concat(axis=-1, values=history)
      core_output, hidden_state = self.core(inputs, batch_input['hidden'])
      actions = self.embedAction(batch_input['delayed_action'])
      
      if self.predict:
        predict_actions = actions[:, :self.model.predict_steps]
        delayed_actions = actions[:, self.model.predict_steps:]
        core_output = self.model.predict(history, core_output, hidden_state, predict_actions, batch_input['state'])
      else:
        delayed_actions = actions
      
      batch_policy = self.policy.getPolicy(core_output, delayed_actions), hidden_state
      self.run_policy = util.deepMap(lambda t: tf.squeeze(t, [0]), batch_policy)

      self.check_op = tf.no_op() if self.dynamic else tf.add_check_numerics_ops()
      
      self._finalize_setup()

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    policy, hidden = self.sess.run([self.run_policy, self.check_op], feed_dict)[0]
    return self.policy.act(policy, verbose), hidden
