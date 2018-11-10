from .RL import RL
import tensorflow as tf
from .default import Option
from . import ssbm, util, ctype_util as ct, embed
from .core import Core
from .ac import ActorCritic
from .critic import Critic
from .search import SearchPolicy

class Actor(RL):
  _options = RL._options + [
    Option('plan_ratio', type=float, default=0.),
  ]
  
  _members = RL._members + [
    ('planner', SearchPolicy),
  ]

  def __init__(self, **kwargs):
    super(Actor, self).__init__(**kwargs)

    with self.graph.as_default(), tf.device(self.device): 
      if self.predict: self._init_model(**kwargs)
      self._init_policy(**kwargs)
      
      if self.plan_ratio > 0:
        self.critic = Critic(self.core.output_size, **kwargs)
        self.planner = SearchPolicy(self.model, self.embedAction, self.critic, **kwargs)

      # build computation graph
      self.input = ct.inputCType(ssbm.SimpleStateAction, [self.config.memory+1], "input")
      self.input['delayed_action'] = tf.placeholder(tf.int64, [self.config.delay], "delayed_action")
      self.input['hidden'] = util.deepMap(lambda size: tf.placeholder(tf.float32, [size], name="input/hidden"), self.core.hidden_size)

      batch_input = util.deepMap(lambda t: tf.expand_dims(t, 0), self.input)

      states = self.embedGame(batch_input['state'])
      prev_actions = self.embedAction(batch_input['prev_action'])
      combined = tf.concat(axis=-1, values=[states, prev_actions])
      history = tf.unstack(combined)
      inputs = tf.concat(axis=-1, values=history)
      core_output, hidden_state = self.core(inputs, batch_input['hidden'])
      actions = self.embedAction(batch_input['delayed_action'])
      residual_state = util.deepMap(lambda t: t[-1], batch_input['state'])
      residual_state = self.embedGame(residual_state, residual=True)
      
      if self.predict:
        predict_actions = actions[:, :self.model.predict_steps]
        delayed_actions = actions[:, self.model.predict_steps:]
        history, core_output, hidden_state, residual_state = self.model.predict(history, core_output, hidden_state, predict_actions, residual_state)
      else:
        delayed_actions = actions
      
      batch_policy = self.policy.getPolicy(core_output, delayed_actions)
      if self.plan_ratio > 0:
        plan_policy = self.planner.get_policy(history, core_output, hidden_state, residual_state)
        batch_policy += self.plan_ratio * (plan_policy - batch_policy)
      self.run_policy = util.deepMap(lambda t: tf.squeeze(t, [0]), (batch_policy, hidden_state))
      
      self._finalize_setup()

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    policy, hidden = self.sess.run(self.run_policy, feed_dict)
    return self.policy.act(policy, verbose), hidden
