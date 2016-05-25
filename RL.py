import tensorflow as tf
import random
import ssbm
import ctypes
import tf_lib as tfl
import util
import ctype_util as ct
import numpy as np
import embed
from dqn import DQN
from actor_critic import ActorCritic
from thompson_dqn import ThompsonDQN
import config
from operator import add, sub
from enum import Enum
from reward import computeRewards

class Mode(Enum):
  TRAIN = 0
  PLAY = 1

models = {model.__name__ : model for model in [DQN, ActorCritic, ThompsonDQN]}

class RLConfig:
  def __init__(self, tdN=5, reward_halflife = 2.0, **kwargs):
    self.tdN = tdN
    self.reward_halflife = reward_halflife
    self.discount = 0.5 ** ( 1.0 / (config.fps*reward_halflife) )

class Model:
  def __init__(self,
              model="DQN",
              path=None,
              mode = Mode.TRAIN,
              debug = False,
              swap=False,
              learning_rate=1e-4,
              **kwargs):
    print("Creating model:", model)
    modelType = models[model]
    
    self.path = path
    
    self.graph = tf.Graph()
    
    with self.graph.as_default():
      
      # TODO: take into account mode
      with tf.name_scope('input'):
        self.input_states = ct.inputCType(ssbm.GameMemory, [None], "state")

        # player 2's controls
        self.input_actions = tf.placeholder(tf.int32, [None], "action")
        #experience_length = tf.shape(input_actions)

      self.embedded_states = embed.embedGame(self.input_states, swap)
      self.state_size = self.embedded_states.get_shape()[-1].value # TODO: precompute

      self.embedded_actions = embed.embedAction(self.input_actions)
      self.action_size = self.embedded_actions.get_shape()[-1].value

      # instantaneous rewards for all but the first state
      self.rewards = tf.placeholder(tf.float32, [None], name='reward')
      
      self.train_dict = {
        'state' : self.input_states,
        'action' : self.input_actions,
        'reward' : self.rewards
      }

      self.global_step = tf.Variable(0, name='global_step', trainable=False)

      self.rlConfig = RLConfig(**kwargs)
      self.model = modelType(self.state_size, self.action_size, self.global_step, self.rlConfig, **kwargs)
      
      if mode == Mode.TRAIN:
        with tf.name_scope('train'):
          loss, stats = self.model.getLoss(self.embedded_states, self.embedded_actions, self.rewards, **kwargs)
          stats.append(('global_step', self.global_step))
          self.stat_names, self.stat_tensors = zip(*stats)

          optimizer = tf.train.AdamOptimizer(learning_rate)
          # train_q = opt.minimize(qLoss, global_step=global_step)
          # opt = tf.train.GradientDescentOptimizer(0.0)
          #grads_and_vars = opt.compute_gradients(qLoss)
          grads_and_vars = optimizer.compute_gradients(loss)
          self.grads_and_vars = [(g, v) for g, v in grads_and_vars if g is not None]
          self.trainer = optimizer.apply_gradients(grads_and_vars, global_step=self.global_step)
          self.runOps = self.stat_tensors + (self.trainer,)
      else:
        with tf.name_scope('policy'):
          # TODO: policy might share graph structure with loss?
          self.policy = self.model.getPolicy(self.embedded_states, **kwargs)

      if mode == Mode.PLAY: # don't eat up cpu cores
        configProto = tf.ConfigProto(
          inter_op_parallelism_threads=1,
          intra_op_parallelism_threads=1,
        )
      else: # or gpu memory
        configProto = tf.ConfigProto(gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.3))
      
      self.sess = tf.Session(
        graph=self.graph,
        config=configProto,
      )
      
      self.debug = debug
      
      self.saver = tf.train.Saver(tf.all_variables())

  def act(self, state, verbose=False):
    feed_dict = ct.feedCTypes(ssbm.GameMemory, 'input/state', [state])
    return self.model.act(self.sess.run(self.policy, feed_dict), verbose)

  #summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
  #summaryWriter.flush()

  def debugGrads(self, feed_dict):
    gs = self.sess.run([gv[0] for gv in self.grads_and_vars], feed_dict)
    vs = self.sess.run([gv[1] for gv in self.grads_and_vars], feed_dict)
    #   loss = sess.run(qLoss, feed_dict)
    #act_qs = sess.run(qs, feed_dict)
    #act_qs = list(map(util.compose(np.sort, np.abs), act_qs))

    #t = sess.run(temperature)
    #print("Temperature: ", t)
    #for i, act in enumerate(act_qs):
    #  print("act_%d"%i, act)
    #print("grad/param(action)", np.mean(np.abs(gs[0] / vs[0])))
    #print("grad/param(stage)", np.mean(np.abs(gs[2] / vs[2])))

    print("param avg and max")
    for g, v in zip(gs, vs):
      abs_v = np.abs(v)
      abs_g = np.abs(g)
      print(v.shape, np.mean(abs_v), np.max(abs_v), np.mean(abs_g), np.max(abs_g))

    print("grad/param avg and max")
    for g, v in zip(gs, vs):
      ratios = np.abs(g / v)
      print(np.mean(ratios), np.max(ratios))
    #print("grad", np.mean(np.abs(gs[4])))
    #print("param", np.mean(np.abs(vs[0])))

    # if step_index == 10:
    import ipdb; ipdb.set_trace()

  def train(self, filename, steps=1):
    #state_actions = ssbm.readStateActions(filename)
    #feed_dict = feedStateActions(state_actions)
    experience = ssbm.readStateActions_pickle(filename)
    
    feed_dict = dict(util.deepValues(util.deepZip(self.train_dict, experience)))

    # FIXME: we feed the inputs in on each iteration, which might be inefficient.
    for step_index in range(steps):
      if self.debug:
        self.debugGrads(feed_dict)
      
      # last result is trainer
      results = self.sess.run(self.runOps, feed_dict)[:-1]
      util.zipWith(print, self.stat_names, results)

    return sum(experience['reward'])

  def save(self):
    import os
    os.makedirs(self.path, exist_ok=True)
    print("Saving to", self.path)
    self.saver.save(self.sess, self.path + "snapshot")

  def restore(self):
    self.saver.restore(self.sess, self.path + "snapshot")

  def init(self):
    with self.graph.as_default():
      self.sess.run(tf.initialize_all_variables())

