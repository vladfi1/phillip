import tensorflow as tf
import ssbm
import ctypes
import tf_lib as tfl
import util

# TODO: fill out the rest of this table
ctypes2TF = {
  ctypes.c_bool : tf.bool,
  ctypes.c_float : tf.float32,
  ctypes.c_double : tf.float64,
  ctypes.c_uint : tf.int32,
}

def inputCType(ctype, shape=None, name=""):
  if ctype in ctypes2TF:
    return tf.placeholder(ctypes2TF[ctype], shape, name)
  elif issubclass(ctype, ctypes.Structure):
    return {f : inputCType(t, shape, name + "/" + f) for (f, t) in ctype._fields_}
  else:
    raise TypeError("Unhandled ctype " + ctype)

def feedCTypes(ctype, input, values, feed_dict=None):
  if feed_dict is None:
    feed_dict = {}
  if ctype in ctypes2TF:
    feed_dict[input] = values
  elif issubclass(ctype, ctypes.Structure):
    for f, t in ctype._fields_:
      feedCTypes(t, input[f], [getattr(c, f) for c in values], feed_dict)
  else:
    raise TypeError("Unhandled ctype " + ctype)
  
  return feed_dict

with tf.name_scope('train'):
  train_states = inputCType(ssbm.GameMemory, [None], "states")

  # player 2's controls
  train_controls = inputCType(ssbm.ControllerState, [None], "controls")

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

playerEmbedding = [
  ("percent", castFloat),
  ("facing", castFloat),
  ("x", embedFloat),
  ("y", embedFloat),
  ("action", embedAction),
  ("action_counter", castFloat),
  ("action_frame", castFloat),
  ("character", one_hot(maxCharacter)),
  ("invulnerable", castFloat),
  ("hitlag_frames_left", castFloat),
  ("hitstun_frames_left", castFloat),
  ("jumps_left", castFloat),
  ("charging_smash", castFloat),
  ("on_ground", castFloat),
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

maxStage = 64 # overestimate
stageSpace = 32

with tf.variable_scope("embed_stage"):
  stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))

gameEmbedding = [
  ('player_one', embedPlayer),
  ('player_two', embedPlayer),

  #('frame', c_uint),
  ('stage', embedStage)
]

embedGame = embedStruct(gameEmbedding)
embedded_states = embedGame(train_states)
state_size = embedded_states.get_shape()[-1].value

controllerEmbedding = [
  ('buttonA', castFloat),
  ('buttonB', castFloat),
  ('buttonX', castFloat),
  ('buttonY', castFloat),
  ('buttonL', castFloat),
  ('buttonR', castFloat),
  
  ('analogL', embedFloat),
  ('analogR', embedFloat),
  
  ('mainX', embedFloat),
  ('mainY', embedFloat),
    
  ('cX', embedFloat),
  ('cY', embedFloat)
]

embedController = embedStruct(controllerEmbedding)
embedded_controls = embedController(train_controls)
control_size = embedded_controls.get_shape()[-1].value
assert(control_size == 12)

with tf.variable_scope("q_net"):
  q1 = tfl.makeAffineLayer(state_size + control_size, 512, tf.tanh)
  q2 = tfl.makeAffineLayer(512, 1)

def q(states, controls):
  state_actions = tf.concat(1, [states, controls])
  return tf.squeeze(q2(q1(state_actions)))

# pre-computed long-term rewards
rewards = tf.placeholder(tf.float32, [None], name='rewards')

with tf.name_scope('trainQ'):
  qPredictions = q(embedded_states, embedded_controls)

  qLosses = tf.squared_difference(qPredictions, rewards)
  qLoss = tf.reduce_sum(qLosses)

  trainQ = tf.train.RMSPropOptimizer(0.0001).minimize(qLoss)

with tf.variable_scope("actor"):
  layers = [state_size, 64, control_size]
  nls = [tf.tanh, tf.sigmoid]
  applyLayers = []
  
  applyC1 = tfl.makeAffineLayer(state_size, 64, tf.tanh)
  # the first 8 members of controllerEmbedding are in [0,1]
  applyC2 = t
  applyC2Sigmoid = tfl.makeAffineLayer(64, 8, tf.sigmoid)
  # the last 4 are in [-1, 1]
  applyC2Tanh = tfl.makeAffineLayer(64, 4, tf.tanh)

actor_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
#print(actor_variables)

def applyActor(states):
  c1 = applyC1(states)
  c2Sigmoid = applyC2Sigmoid(c1)
  c2Tanh = applyC2Tanh(c1)
  return tf.concat(1, [c2Sigmoid, c2Tanh])

with tf.name_scope("actorQ"):
  actions = applyActor(embedded_states)
  actorQ = tf.reduce_sum(q(embedded_states, actions))

#trainActor = tf.train.RMSPropOptimizer(0.001).minimize(-actorQ)
trainActor = tf.train.RMSPropOptimizer(0.001).minimize(-actorQ, var_list=actor_variables)

def deepMapDict(f, d):
  if isinstance(d, dict):
    return {k : deepMapDict(f, v) for k, v in d.items()}
  return f(d)

with tf.name_scope('predict'):
  predict_state = inputCType(ssbm.GameMemory, [], "state")
  reshaped = deepMapDict(lambda t: tf.reshape(t, [1]), predict_state)
  embedded_state = embedGame(reshaped)
  
  embedded_action = tf.squeeze(applyActor(embedded_state))
  #split = tf.split(0, 12, embedded_action, name='action')

sess = tf.Session()

#summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
#summaryWriter.flush()

saver = tf.train.Saver(tf.all_variables())

# see GameState.h for explanations
dyingActions = set([0x0, 0x1, 0x2, 0x4, 0x6, 0x7, 0x8])

def isDying(player):
  return player.action in dyingActions

# players tend to be dead for many frames in a row
# here we prune a all but the first frame of the death
def processDeaths(deaths):
  return util.zipWith(lambda prev, next: (not prev) and next, [False] + deaths[:-1] , deaths)

# from player 2's perspective
def computeRewards(states, discount = 0.99):
  kills = [isDying(state.player_one) for state in states]
  deaths = [isDying(state.player_two) for state in states]
  
  kills = processDeaths(kills)
  deaths = processDeaths(deaths)
  
  scores = util.zipWith(lambda x, y: x - y, kills, deaths)
  
  return util.scanr1(lambda r1, r2: r1 + discount * r2, scores)
  
def readFile(filename, states=None, controls=None):
  if states is None:
    states = []
  if controls is None:
    controls = []
  
  with open('testRecord0', 'rb') as f:
    for i in range(60 * 60):
      states.append(ssbm.GameMemory())
      f.readinto(states[-1])
      
      controls.append(ssbm.ControllerState())
      f.readinto(controls[-1])
    
    # should be zero
    # print(len(f.read()))
  
  return states, controls

def train(filename):
  states, controls = readFile(filename)
  
  feed_dict = {rewards : computeRewards(states)}
  feedCTypes(ssbm.GameMemory, train_states, states, feed_dict)
  feedCTypes(ssbm.ControllerState, train_controls, controls, feed_dict)
  
  print(sess.run(qLoss, feed_dict))
  
  for _ in range(10):
    for _ in range(10):
      sess.run([trainQ, trainActor], feed_dict)
    print(sess.run([qLoss, actorQ], feed_dict))
  
  saver.save(sess, 'simpleDQN')

sess.run(tf.initialize_all_variables())
train('testRecord0')

