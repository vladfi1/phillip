import tensorflow as tf
import random
import ssbm
import ctypes
import tf_lib as tfl
import util
import ctype_util as ct
import numpy as np

with tf.name_scope('input'):
  input_states = ct.inputCType(ssbm.GameMemory, [None], "states")

  # player 2's controls
  input_controls = ct.inputCType(ssbm.SimpleControllerState, [None], "controls")

def feedStateActions(states, actions, feed_dict = None):
  if feed_dict is None:
    feed_dict = {}
  ct.feedCTypes(ssbm.GameMemory, 'input/states', states, feed_dict)
  ct.feedCTypes(ssbm.SimpleControllerState, 'input/controls', actions, feed_dict)
  return feed_dict

embedFloat = lambda t: tf.reshape(t, [-1, 1])

castFloat = lambda t: embedFloat(tf.cast(t, tf.float32))

def one_hot(size):
  def clamp(input):
    return tf.minimum(tf.maximum(input, 0), size)
  return lambda t: tf.one_hot(clamp(tf.cast(t, tf.int64)), size, 1.0, 0.0)

maxAction = 512 # altf4 says 0x017E
actionSpace = 32

maxCharacter = 32 # should be large enough?

maxJumps = 8 # unused

with tf.variable_scope("embed_action"):
  actionHelper = tfl.makeAffineLayer(maxAction, actionSpace)

def embedAction(t):
  return actionHelper(one_hot(maxAction)(t))

def rescale(a):
  return lambda x: a * x

playerEmbedding = [
  ("percent", util.compose(rescale(0.01), castFloat)),
  ("facing", embedFloat),
  ("x", util.compose(rescale(0.1), embedFloat)),
  ("y", util.compose(rescale(0.1), embedFloat)),
  ("action_state", embedAction),
  # ("action_counter", castFloat),
  ("action_frame", util.compose(rescale(0.02), castFloat)),
  # ("character", one_hot(maxCharacter)),
  ("invulnerable", castFloat),
  ("hitlag_frames_left", castFloat),
  ("hitstun_frames_left", castFloat),
  ("jumps_used", castFloat),
  ("charging_smash", castFloat),
  ("in_air", castFloat),
  ('speed_air_x_self',  embedFloat),
  ('speed_ground_x_self', embedFloat),
  ('speed_y_self', embedFloat),
  ('speed_x_attack', embedFloat),
  ('speed_y_attack', embedFloat)
]

# TODO: give the tensors some names/scopes
def embedStruct(embedding):
  def f(struct):
    embed = [op(struct[field]) for field, op in embedding]
    return tf.concat(1, embed)
  return f

embedPlayer = embedStruct(playerEmbedding)

def embedArray(embed, indices=None):

  def f(array):
    return tf.concat(1, [embed(array[i]) for i in indices])
  return f

"""
maxStage = 64 # overestimate
stageSpace = 32

with tf.variable_scope("embed_stage"):
  stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))
"""

gameEmbedding = [
  ('players', embedArray(embedPlayer, [0, 1])),

  #('frame', c_uint),
  # ('stage', embedStage)
]

embedGame = embedStruct(gameEmbedding)
embedded_states = embedGame(input_states)
state_size = embedded_states.get_shape()[-1].value

stickEmbedding = [
  ('x', embedFloat),
  ('y', embedFloat)
]

embedStick = embedStruct(stickEmbedding)

controllerEmbedding = [
  ('button_A', castFloat),
  ('button_B', castFloat),
  ('button_X', castFloat),
  ('button_Y', castFloat),
  ('button_L', castFloat),
  ('button_R', castFloat),

  ('trigger_L', embedFloat),
  ('trigger_R', embedFloat),

  ('stick_MAIN', embedStick),
  ('stick_C', embedStick),
]

embedController = embedStruct(controllerEmbedding)

def embedEnum(enum):
  return one_hot(len(enum))

simpleControllerEmbedding = [
  ('button', embedEnum(ssbm.SimpleButton)),
  ('stick_MAIN', embedEnum(ssbm.SimpleStick)),
]

embedSimpleController = embedStruct(simpleControllerEmbedding)

#embedded_controls = embedController(train_controls)
embedded_controls = embedSimpleController(input_controls)
control_size = embedded_controls.get_shape()[-1].value
assert(control_size == 7)

with tf.variable_scope("q_net"):
  layers = [state_size+control_size, 128, 128]
  applyQs = [tfl.makeAffineLayer(prev, next, tfl.leaky_relu) for prev, next in zip(layers[:-1], layers[1:])]
  #q1 = tfl.makeAffineLayer(state_size + control_size, 512, tf.tanh)
  applyQs.append(util.compose(tf.squeeze, tfl.makeAffineLayer(layers[-1], 1)))

def applyQ(states, controls):
  """Applies the q network, returning all intermediate layers in order.
  The last returned value is the final q prediction."""
  state_actions = tf.concat(1, [states, controls])
  outputs = [state_actions]
  for i, f in enumerate(applyQs):
    with tf.name_scope('q%d' % i):
      outputs.append(f(outputs[-1]))

  return outputs

# pre-computed long-term rewards
rewards = tf.placeholder(tf.float32, [None], name='rewards')

global_step = tf.Variable(0, name='global_step', trainable=False)

with tf.name_scope('train_q'):
  qs = applyQ(embedded_states, embedded_controls)
  qOut = qs[-1]

  qLosses = tf.squared_difference(qs[-1], rewards)
  qLoss = tf.reduce_mean(qLosses)

  #trainQ = tf.train.RMSPropOptimizer(0.0001).minimize(qLoss)

  opt = tf.train.AdamOptimizer(10.0 ** -5)
  # train_q = opt.minimize(qLoss, global_step=global_step)
  # opt = tf.train.GradientDescentOptimizer(0.0)
  grads_and_vars = opt.compute_gradients(qLoss)
  train_q = opt.apply_gradients(grads_and_vars, global_step=global_step)

with tf.name_scope('epsilon'):
  epsilon = tf.maximum(0.05, 0.7 - tf.cast(global_step, tf.float32) / 5000000.0)

def getEpsilon():
  return sess.run(epsilon)

with tf.name_scope('temperature'):
  temperature = 20.0 * 0.5 ** (tf.cast(global_step, tf.float32) / 1000.0) + 1.0

with tf.name_scope('actor'):
  actor_state = ct.inputCType(ssbm.GameMemory, [], 'state')
  reshaped = util.deepMap(lambda t: tf.reshape(t, [1]), actor_state)
  embedded_state = embedGame(reshaped)
  tiled = tf.tile(embedded_state, [len(ssbm.simpleControllerStates), 1])

  all_actions = ct.constantCTypes(ssbm.SimpleControllerState, ssbm.simpleControllerStates, 'all_actions')
  embedded_actions = embedSimpleController(all_actions)

  all_scores = applyQ(tiled, embedded_actions)[-1]

sess = tf.Session()

#summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
#summaryWriter.flush()

saver = tf.train.Saver(tf.all_variables())

#def predictAction(state):
#  feed_dict = tfl.feedCType(ssbm.GameMemory, 'predict/state', state)
#  return sess.run('predict/action:0', feed_dict)

def predictQ(states, controls):
  return sess.run(qOut, feedStateActions(states, controls))

# TODO: do this within the tf model?
# if we do, then we can add in softmax and temperature
def scoreActions(state):
  return sess.run(all_scores, ct.feedCType(ssbm.GameMemory, 'actor/state', state))

# see https://docs.google.com/spreadsheets/d/1JX2w-r2fuvWuNgGb6D3Cs4wHQKLFegZe2jhbBuIhCG8/edit#gid=13
dyingActions = set(range(0xA))

def isDying(player):
  return player.action_state in dyingActions

# players tend to be dead for many frames in a row
# here we prune all but the first frame of the death
def processDeaths(deaths):
  return util.zipWith(lambda prev, next: (not prev) and next, [False] + deaths[:-1] , deaths)

# from player 2's perspective
def computeRewards(states, reward_halflife = 2.0):
  # reward_halflife is measured in seconds
  fps = 60.0 / 5.0
  discount = 0.5 ** ( 1.0 / (fps*reward_halflife) )

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

  print("Damage dealt for current memory: ", sum(damage_dealt))
  print("Damage taken for current memory: ", sum(damage_taken))
  print("Scores for current memory: ", final_scores[:10])

  # use last action taken?
  lastQ = max(scoreActions(states[-1]))
  print("lastQ", lastQ)

  discounted_rewards = util.scanr(lambda r1, r2: r1 + discount * r2, lastQ, final_scores)[:-1]

  print("discounted_rewards for current memory: ", discounted_rewards[:10])
  return discounted_rewards

debug = False

def train(filename, steps=1):
  states, controls = zip(*ssbm.readStateActions(filename))
  r = computeRewards(states)
  feed_dict = {rewards : r}
  feedStateActions(states[:-1], controls[:-1], feed_dict)

  # FIXME: we feed the inputs in on each iteration, which might be inefficient.
  for step_index in range(steps):
    if debug:
      gs = sess.run([gv[0] for gv in grads_and_vars], feed_dict)
      vs = sess.run([gv[1] for gv in grads_and_vars], feed_dict)
      #   loss = sess.run(qLoss, feed_dict)
      act_qs = sess.run(qs, feed_dict)
      act_qs = list(map(util.compose(np.sort, np.abs), act_qs))

      #t = sess.run(temperature)
      #print("Temperature: ", t)
      for i, act in enumerate(act_qs):
        print("act_%d"%i, act)
      print("grad/param(action)", np.mean(np.abs(gs[0] / vs[0])))
      #print("grad/param(stage)", np.mean(np.abs(gs[2] / vs[2])))
      for i in range(len(layers)):
        j = 2 * (i+1)
        print("grad/param(q%d)" % (i+1), np.mean(np.abs(gs[j] / vs[j])))
      #print("grad", np.mean(np.abs(gs[4])))
      #print("param", np.mean(np.abs(vs[0])))

      # if step_index == 10:
      import pdb; pdb.set_trace()

    # print(sum(gvs))
    #sess.run([train_q, trainActor], feed_dict)
    sess.run(train_q, feed_dict)

    # sess.run(trainQ, feed_dict)
    #sess.run(trainActor, feed_dict)
  #print(sess.run([qLoss, actorQ], feed_dict))
  print("qLoss", sess.run(qLoss, feed_dict))
  return sum(r)

def save(name):
  save_location = "saves/" + name + "/snapshot"
  print("Saving to", save_location)
  saver.save(sess, save_location)

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
