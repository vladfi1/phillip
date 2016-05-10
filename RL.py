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

#----- set up inputs and model -----------
with tf.name_scope('input'):
  input_states = ct.inputCType(ssbm.GameMemory, [None], "states")

  # player 2's controls
  #input_controls = ct.inputCType(ssbm.SimpleControllerState, [None], "controls")
  input_controls = tf.placeholder(tf.int32, [None], "controls")
  experience_length = tf.shape(input_controls)

embedded_states = embed.embedGame(input_states)
state_size = embedded_states.get_shape()[-1].value

control_size = len(ssbm.simpleControllerStates)
embedded_controls = tfl.one_hot(control_size)(input_controls)
#embedded_controls = embed.embedSimpleController(input_controls)
#control_size = embedded_controls.get_shape()[-1].value
#assert(control_size == 7)


model = DQN(state_size, control_size)
#---------------------------------------


def feedStateActions(states, actions, feed_dict = None):
  if feed_dict is None:
    feed_dict = {}
  ct.feedCTypes(ssbm.GameMemory, 'input/states', states, feed_dict)
  #ct.feedCTypes(ssbm.SimpleControllerState, 'input/controls', actions, feed_dict)
  feed_dict[input_controls] = actions
  return feed_dict

# instantaneous rewards for all but the first state
rewards = tf.placeholder(tf.float32, [None], name='rewards')

global_step = tf.Variable(0, name='global_step', trainable=False)

n = 5
train_length = experience_length - n

reward_halflife = 2.0 # seconds
act_every = 5 # needs to match agent
fps = 60.0 / act_every
discount = 0.5 ** ( 1.0 / (fps*reward_halflife) )

with tf.name_scope('train_q'):
  #embedded_input = tf.concat(1, [embedded_states, embedded_controls])
  qValues = model.getQValues(embedded_states)
  realQs = tf.reduce_sum(tf.mul(qValues, embedded_controls), 1)
  maxQs = tf.stop_gradient(tf.reduce_max(qValues, 1))

  targets = tf.slice(maxQs, [n], train_length)
  for i in reversed(range(n)):
    targets = tf.slice(rewards, [i], train_length) + discount * targets

  #qLoss = model.getNLLQLoss(embedded_input, rewards)
  trainQs = tf.slice(realQs, [0], train_length)
  qLosses = tf.squared_difference(trainQs, targets)
  qLoss = tf.reduce_mean(qLosses)

  opt = tf.train.AdamOptimizer(10.0 ** -6)
  # train_q = opt.minimize(qLoss, global_step=global_step)
  # opt = tf.train.GradientDescentOptimizer(0.0)
  grads_and_vars = opt.compute_gradients(qLoss)
  train_q = opt.apply_gradients(grads_and_vars, global_step=global_step)

with tf.name_scope('epsilon'):
  epsilon = tf.maximum(0.05, 0.7 - tf.cast(global_step, tf.float32) / 5000000.0)

def getEpsilon():
  return sess.run(epsilon)

with tf.name_scope('temperature'):
  #temperature = 0.05  * (0.5 ** (tf.cast(global_step, tf.float32) / 100000.0) + 0.1)
  temperature = tf.constant(0.01)

def getTemperature():
  return sess.run(temperature)

with tf.name_scope('get_action'):
  actor_state = ct.inputCType(ssbm.GameMemory, [], 'state')
  reshaped = util.deepMap(lambda t: tf.reshape(t, [1]), actor_state)
  embedded_state = embed.embedGame(reshaped)

  mu, log_sigma2 = model.getQDists(embedded_state)
  action_probs = tf.squeeze(tf.nn.softmax(mu / temperature))
  mu = tf.squeeze(mu)
  log_sigma2 = tf.squeeze(log_sigma2)

#sess = tf.Session()
# don't eat up cpu cores
sess = tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=1,
                                        intra_op_parallelism_threads=1,
                                        use_per_session_threads=True))

#summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
#summaryWriter.flush()

saver = tf.train.Saver(tf.all_variables())

def scoreActions(state):
  return sess.run(mu, ct.feedCType(ssbm.GameMemory, 'get_action/state', state))

def getActionProbs(state):
  return sess.run(action_probs, ct.feedCType(ssbm.GameMemory, 'get_action/state', state))

def getActionDists(state):
  return sess.run([mu, log_sigma2], ct.feedCType(ssbm.GameMemory, 'get_action/state', state))

# see https://docs.google.com/spreadsheets/d/1JX2w-r2fuvWuNgGb6D3Cs4wHQKLFegZe2jhbBuIhCG8/edit#gid=13
dyingActions = set(range(0xA))

def isDying(player):
  return player.action_state in dyingActions

# players tend to be dead for many frames in a row
# here we prune all but the first frame of the death
def processDeaths(deaths):
  return util.zipWith(lambda prev, next: (not prev) and next, [False] + deaths[:-1] , deaths)

# from player 2's perspective
def computeRewards(states):
  kills = [isDying(state.players[0]) for state in states]
  deaths = [isDying(state.players[1]) for state in states]

  # print(states[random.randint(0, len(states))].players[0])

  kills = processDeaths(kills)
  deaths = processDeaths(deaths)
  # print("Deaths for current memory: ", sum(deaths))
  # print("Kills for current memory: ", sum(kills))

  damage_dealt = [max(states[i+1].players[0].percent - states[i].players[0].percent, 0) for i in range(len(states)-1)]
  damage_taken = [max(states[i+1].players[1].percent - states[i].players[1].percent, 0) for i in range(len(states)-1)]



  # damage_dealt = util.zipWith(lambda prev, next: max(next.players[0].percent - prev.players[0].percent, 0), states[:-1], states[1:])

  scores = util.zipWith(lambda k, d: k - d, kills[1:], deaths[1:])
  final_scores = util.zipWith(lambda score, dealt, taken: score + (dealt - taken) / 100, scores, damage_dealt, damage_taken)

  print("Damage dealt: ", sum(damage_dealt))
  print("Damage taken: ", sum(damage_taken))
  print("Total score: ", sum(final_scores))

  return final_scores

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

    # print(sum(gvs))
    #sess.run([train_q, trainActor], feed_dict)
    sess.run(train_q, feed_dict)

    # sess.run(trainQ, feed_dict)
    #sess.run(trainActor, feed_dict)
  #print(sess.run([qLoss, actorQ], feed_dict))
  print("qLoss", sess.run(qLoss, feed_dict))
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
