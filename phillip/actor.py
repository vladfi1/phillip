from phillip import RL
import tensorflow as tf
from . import ssbm, util, ctype_util as ct, embed
from .core import Core
from .ac import ActorCritic

class Actor(RL.RL):
  def __init__(self, debug=False, **kwargs):
    super(Actor, self).__init__(debug=debug, **kwargs)

    self.graph = tf.Graph()
    device = '/gpu:0' if self.gpu else '/cpu:0'
    print("Using device " + device)
    with self.graph.as_default(), tf.device(device): 
      # total number of gradient descent steps the learner has taken thus far
      self.global_step = tf.Variable(0, name='global_step', trainable=False)
      self.evo_variables = []
      
      self.embedGame = embed.GameEmbedding(**kwargs)
      state_size = self.embedGame.size
      combined_size = state_size + self.embedAction.size
      history_size = (1+self.config.memory) * combined_size
      print("History size:", history_size)

      self.core = Core(history_size, **kwargs)
      
      if self.predict:
        print("Creating model.")
        self.model = Model(self.embedGame, self.embedAction.size, self.core, self.config, **kwargs)
        self.predict = True

      effective_delay = self.config.delay
      if self.predict:
        effective_delay -= self.model.predict_steps
      input_size = self.core.output_size + effective_delay * self.embedAction.size
      
      self.policy = ActorCritic(input_size, self.embedAction.size, self.config, **kwargs)
      self.evo_variables.extend(self.policy.evo_variables)
      
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
      
      self.debug = debug

      self.variables = tf.global_variables()
      self.initializer = tf.global_variables_initializer()
      
      self.saver = tf.train.Saver(self.variables)
      
      self.placeholders = {v.name : tf.placeholder(v.dtype, v.get_shape()) for v in self.variables}
      self.unblobber = tf.group(*[tf.assign(v, self.placeholders[v.name]) for v in self.variables])
      
      self.graph.finalize()
      
      tf_config = dict(
        allow_soft_placement=True,
        #log_device_placement=True,
      )
      
      if self.save_cpu:
        tf_config.update(
          inter_op_parallelism_threads=1,
          intra_op_parallelism_threads=1,
        )
      
      self.sess = tf.Session(
        graph=self.graph,
        config=tf.ConfigProto(**tf_config),
      )
      
      if self.tfdbg:
        from tensorflow.python import debug as tf_debug
        self.sess = tf_debug.LocalCLIDebugWrapperSession(self.sess)

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    policy, hidden = self.sess.run(self.run_policy, feed_dict)
    return self.policy.act(policy, verbose), hidden

  # for unserializing updated weights sent from learners. 
  def unblob(self, blob):
    #self.sess.run(self.unblobber, {self.placeholders[k]: v for k, v in blob.items()})
    self.sess.run(self.unblobber, {v: blob[k] for k, v in self.placeholders.items()})