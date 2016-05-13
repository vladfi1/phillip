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
import config
from operator import add, sub

#----- set up inputs and model -----------
with tf.name_scope('input'):
  input_states = ct.inputCType(ssbm.GameMemory, [None], "states")

  # player 2's controls
  input_actions = tf.placeholder(tf.int32, [None], "actions")
  experience_length = tf.shape(input_actions)

embedded_states = embed.embedGame(input_states)
state_size = embedded_states.get_shape()[-1].value

embedded_actions = embed.embedAction(input_actions)

model = ActorCritic(state_size, embed.action_size)
#---------------------------------------

def feedStateActions(states, actions, feed_dict = None):
  if feed_dict is None:
    feed_dict = {}
  ct.feedCTypes(ssbm.GameMemory, 'input/states', states, feed_dict)
  feed_dict[input_actions] = actions
  return feed_dict

# instantaneous rewards for all but the first state
rewards = tf.placeholder(tf.float32, [None], name='rewards')

global_step = tf.Variable(0, name='global_step', trainable=False)

with tf.name_scope('temperature'):
  #temperature = 0.05  * (0.5 ** (tf.cast(global_step, tf.float32) / 100000.0) + 0.1)
  temperature = tf.constant(0.01)

with tf.name_scope('epsilon'):
  #epsilon = tf.constant(0.02)
  epsilon = 0.04 + 0.5 * tf.exp(-tf.cast(global_step, tf.float32) / 50000.0)

# TD(n)
n = 5

reward_halflife = 2.0 # seconds
discount = 0.5 ** ( 1.0 / (config.fps*reward_halflife) )

train_length = experience_length - n

values, actor = model.getOutput(embedded_states)
trainVs = tf.slice(values, [0], train_length)

actor_probs = tf.nn.softmax(actor)
actor_probs = (1 - epsilon) * actor_probs + epsilon / embed.action_size

# smooth between TD(m) for m<=n?
targets = tf.slice(values, [n], train_length)
for i in reversed(range(n)):
  targets = tf.slice(rewards, [i], train_length) + discount * targets
targets = tf.stop_gradient(targets)

advantages = targets - trainVs
vLoss = tf.reduce_mean(tf.square(advantages))

log_actor_probs = tf.log(actor_probs)
actor_entropy = tf.reduce_mean(tfl.batch_dot(actor_probs, log_actor_probs))
real_log_actor_probs = tfl.batch_dot(embedded_actions, tf.log(actor_probs))
train_log_actor_probs = tf.slice(real_log_actor_probs, [0], train_length)
actor_gain = tf.reduce_mean(tf.mul(train_log_actor_probs, tf.stop_gradient(advantages)))

acLoss = vLoss - actor_gain# + actor_entropy

opt = tf.train.AdamOptimizer(10.0 ** -4)
# train_q = opt.minimize(qLoss, global_step=global_step)
# opt = tf.train.GradientDescentOptimizer(0.0)
#grads_and_vars = opt.compute_gradients(qLoss)
grads_and_vars = opt.compute_gradients(acLoss)
grads_and_vars = [(g, v) for g, v in grads_and_vars if g is not None]
train_q = opt.apply_gradients(grads_and_vars, global_step=global_step)


# don't eat up cpu cores
# or gpu memory
sess = tf.Session(
  config=tf.ConfigProto(
    inter_op_parallelism_threads=1,
    intra_op_parallelism_threads=1,
    use_per_session_threads=True,
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.3)
  )
)

#summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
#summaryWriter.flush()

saver = tf.train.Saver(tf.all_variables())

def getEpsilon():
  return sess.run(epsilon)

def getTemperature():
  return sess.run(temperature)

def scoreActions(state):
  feed_dict = ct.feedCTypes(ssbm.GameMemory, 'input/states', [state])
  return sess.run(qMeans, feed_dict)[0]

def getActionProbs(state):
  feed_dict = ct.feedCTypes(ssbm.GameMemory, 'input/states', [state])
  return sess.run(softmax_probs, feed_dict)[0]

def getActionDists(state):
  feed_dict = ct.feedCTypes(ssbm.GameMemory, 'input/states', [state])
  mu, log_sigma2 = sess.run([qMeans, qLogVariances], feed_dict)
  return (mu[0], log_sigma2[0])

def getActorProbs(state):
  feed_dict = ct.feedCTypes(ssbm.GameMemory, 'input/states', [state])
  return sess.run(actor_probs, feed_dict)[0]

# see https://docs.google.com/spreadsheets/d/1JX2w-r2fuvWuNgGb6D3Cs4wHQKLFegZe2jhbBuIhCG8/edit#gid=13
dyingActions = set(range(0xA))

def isDying(player):
  return player.action_state in dyingActions

# players tend to be dead for many frames in a row
# here we prune all but the first frame of the death
def processDeaths(deaths):
  return np.array(util.zipWith(lambda prev, next: float((not prev) and next), deaths, deaths[1:]))

def processDamages(percents):
  return np.array(util.zipWith(lambda prev, next: max(next-prev, 0), percents, percents[1:]))

# from player 2's perspective
def computeRewards(states, enemies=[0], allies=[1], damage_ratio=0.01):
  players = enemies + allies

  deaths = {p : processDeaths([isDying(s.players[p]) for s in states]) for p in players}
  damages = {p : processDamages([s.players[p].percent for s in states]) for p in players}

  losses = {p : deaths[p] + damage_ratio * damages[p] for p in players}

  return sum(losses[p] for p in enemies) - sum(losses[p] for p in allies)

debug = False

def train(filename, steps=1):
  state_actions = ssbm.readStateActions(filename)
  states = list(map(lambda x: x.state, state_actions))
  actions = list(map(lambda x: x.action, state_actions))

  r = computeRewards(states)
  feed_dict = {rewards : r}
  feedStateActions(states, actions, feed_dict)

  # FIXME: we feed the inputs in on each iteration, which might be inefficient.
  for step_index in range(steps):
    if debug:
      gs = sess.run([gv[0] for gv in grads_and_vars], feed_dict)
      vs = sess.run([gv[1] for gv in grads_and_vars], feed_dict)
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

    g, q, a, e, _ = sess.run([global_step, vLoss, actor_gain, actor_entropy, train_q], feed_dict)

    print("global_step", g)
    print("vLoss", q)
    print("actor_gain", a)
    print("entropy", e)

  return sum(r)

def save(name):
  save_dir = "saves/%s/" % name
  import os
  os.makedirs(save_dir, exist_ok=True)
  print("Saving to", save_dir)
  saver.save(sess, save_dir + 'snapshot')

def restore(name):
  save_location = "saves/" + name + "/snapshot"
  saver.restore(sess, save_location)

def writeGraph():
  import os
  graph_def = tf.python.client.graph_util.convert_variables_to_constants(sess, sess.graph_def, ['predict/action'])
  tf.train.write_graph(graph_def, 'models/', 'simpleDQN.pb.temp', as_text=False)
  try:
    os.remove('models/simpleDQN.pb')
  except:
      print("No previous model file.")
  os.rename('models/simpleDQN.pb.temp', 'models/simpleDQN.pb')

def init():
  sess.run(tf.initialize_all_variables())
#train('testRecord0')

#saver.restore(sess, 'saves/simpleDQN')
#writeGraph()
