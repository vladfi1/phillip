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
  return lambda t: tf.one_hot(tf.cast(t, tf.int64), size, 1.0, 0.0)

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
  ("x", util.compose(rescale(0.01), embedFloat)),
  ("y", util.compose(rescale(0.01), embedFloat)),
  ("action_state", embedAction),
  # ("action_counter", castFloat),
  ("action_frame", util.compose(rescale(0.02), castFloat)),
  ("character", one_hot(maxCharacter)),
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

maxStage = 64 # overestimate
stageSpace = 32

with tf.variable_scope("embed_stage"):
  stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))

gameEmbedding = [
  ('players', embedArray(embedPlayer, [0, 1])),

  #('frame', c_uint),
  ('stage', embedStage)
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
  q1 = tfl.makeAffineLayer(state_size + control_size, 512, tf.tanh)
  q2 = tfl.makeAffineLayer(512, 1)

def q(states, controls):
  state_actions = tf.concat(1, [states, controls])
  with tf.name_scope('q1'):
    q1_layer = q1(state_actions)
  return tf.squeeze(q2(q1_layer), name='q_out'), q1_layer

# pre-computed long-term rewards
rewards = tf.placeholder(tf.float32, [None], name='rewards')

global_step = tf.Variable(0, name='global_step', trainable=False)

with tf.name_scope('train_q'):
  qPredictions, q1_predict = q(embedded_states, embedded_controls)

  qLosses = tf.squared_difference(qPredictions, rewards)
  qLoss = tf.reduce_mean(qLosses)

  #trainQ = tf.train.RMSPropOptimizer(0.0001).minimize(qLoss)

  opt = tf.train.AdamOptimizer()
  # train_q = opt.minimize(qLoss, global_step=global_step)
  # opt = tf.train.GradientDescentOptimizer(0.0)
  grads_and_vars = opt.compute_gradients(qLoss)
  train_q = opt.apply_gradients(grads_and_vars, global_step=global_step)

with tf.name_scope('epsilon'):
  epsilon = tf.maximum(0.05, 0.7 - tf.cast(global_step, tf.float32) / 5000000.0)

def getEpsilon():
  return sess.run(epsilon)

#with tf.name_scope('temperature'):
#  temperature = 20.0 * 0.5 ** (tf.cast(global_step, tf.float32) / 1000.0) + 1.0

""" no more actor
with tf.variable_scope("actor"):
  layers = [state_size, 64]

  nls = [tf.tanh] * (len(layers) - 1)

  zip_layers = zip(layers[:-1], layers[1:])

  applyLayers = [tfl.makeAffineLayer(prev, next, nl) for (prev, next), nl in zip(zip_layers, nls)]

  button_layer = tfl.makeAffineLayer(layers[-1], len(ssbm.SimpleButton._fields_), util.compose(tf.nn.softmax, lambda x: x / temperature))

  stick_layer = tfl.makeAffineLayer(layers[-1], len(ssbm.SimpleStick._fields_), util.compose(tf.nn.softmax, lambda x: x / temperature))

def applyActor(state):
  for f in applyLayers:
    state = f(state)
  button_state = button_layer(state)
  stick_state = stick_layer(state)

  return tf.concat(1, [button_state, stick_state])

actor_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
#print(actor_variables)

with tf.name_scope("actorQ"):
  actions = applyActor(embedded_states)
  actorQ = tf.reduce_mean(q(embedded_states, actions)[0])

#trainActor = tf.train.RMSPropOptimizer(0.001).minimize(-actorQ)
# FIXME: is this the right sign?
#trainActor = tf.train.RMSPropOptimizer(0.0001).minimize(-actorQ, var_list=actor_variables)

# trainActor = tf.train.AdamOptimizer().minimize(-actorQ, var_list=actor_variables)
actor_opt = tf.train.AdamOptimizer()
actor_grads_and_vars = opt.compute_gradients(-actorQ, var_list=actor_variables)
trainActor = opt.apply_gradients(actor_grads_and_vars, global_step=global_step)

def deepMap(f, obj):
  if isinstance(obj, dict):
    return {k : deepMap(f, v) for k, v in obj.items()}
  if isinstance(obj, list):
    return [deepMap(f, x) for x in obj]
  return f(obj)

with tf.name_scope('predict'):
  predict_state = inputCType(ssbm.GameMemory, [None], 'state')
  #reshaped = deepMap(lambda t: tf.reshape(t, [1]), predict_input_state)
  embedded_state = embedGame(predict_state)
  
  predict_action = inputCType(ssbm.SimpleControllerState, [None], 'action')
  e
"""

sess = tf.Session()

#summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
#summaryWriter.flush()

saver = tf.train.Saver(tf.all_variables())

#def predictAction(state):
#  feed_dict = tfl.feedCType(ssbm.GameMemory, 'predict/state', state)
#  return sess.run('predict/action:0', feed_dict)

def predictQ(states, controls):
  return sess.run(qPredictions, feedStateActions(states, controls))

# TODO: do this within the tf model?
# if we do, then we can add in softmax and temperature
def scoreActions(state):
  return predictQ([state] * len(ssbm.simpleControllerStates), ssbm.simpleControllerStates)

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

  discounted_rewards = util.scanr(lambda r1, r2: r1 + discount * r2, lastQ, final_scores)[:-1]

  print("discounted_rewards for current memory: ", discounted_rewards[:10])
  return discounted_rewards

def train(filename, steps=1):
  states, controls = zip(*ssbm.readStateActions(filename))

  feed_dict = {rewards : computeRewards(states)}
  feedStateActions(states[:-1], controls[:-1], feed_dict)

  # FIXME: we feed the inputs in on each iteration, which might be inefficient.
  for step_index in range(steps):
    if False:
      gs = sess.run([gv[0] for gv in grads_and_vars], feed_dict)
      vs = sess.run([gv[1] for gv in grads_and_vars], feed_dict)
      #   loss = sess.run(qLoss, feed_dict)
      act_4 = sess.run(q1_predict, feed_dict)
      act_4 = np.sort(np.abs(act_4))

      #t = sess.run(temperature)
      #print("Temperature: ", t)
      print("act_4", act_4)
      print("grad/param(action)", np.mean(np.abs(gs[0] / vs[0])))
      print("grad/param(stage)", np.mean(np.abs(gs[2] / vs[2])))
      print("grad/param(q1)", np.mean(np.abs(gs[4] / vs[4])))
      print("grad/param(q2)", np.mean(np.abs(gs[6] / vs[6])))
      print("grad", np.mean(np.abs(gs[4])))
      print("param", np.mean(np.abs(vs[0])))

      # if step_index == 10:
      import pdb; pdb.set_trace()

    # print(sum(gvs))
    #sess.run([train_q, trainActor], feed_dict)
    sess.run(train_q, feed_dict)

    # sess.run(trainQ, feed_dict)
    #sess.run(trainActor, feed_dict)
  #print(sess.run([qLoss, actorQ], feed_dict))
  print("qLoss", sess.run(qLoss, feed_dict))

def save(filename='saves/simpleDQN'):
  print("Saving to", filename)
  saver.save(sess, filename)

def restore(filename='saves/simpleDQN'):
  saver.restore(sess, filename)

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
