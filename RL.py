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

# TODO: use tensorflow variable scopes?
def inputCType(ctype, shape=None, name=""):
  if ctype in ctypes2TF:
    return tf.placeholder(ctypes2TF[ctype], shape, name)
  elif issubclass(ctype, ctypes.Structure):
    return {f : inputCType(t, shape, name + "." + f) for (f, t) in ctype._fields_}
  else:
    raise TypeError("Unhandled ctype " + ctype)

def feedCTypes(ctype, input, values, feed_dict={}):
  if ctype in ctypes2TF:
    feed_dict[input] = values
  elif issubclass(ctype, ctypes.Structure):
    for f, t in ctype._fields_:
      feedCTypes(t, input[f], [getattr(c, f) for c in values], feed_dict)
  else:
    raise TypeError("Unhandled ctype " + ctype)
  
  return feed_dict

input_states = inputCType(ssbm.GameMemory, [None], "input_states")

# player 2's controls
input_controls = inputCType(ssbm.ControllerState, [None], "input_controls")

embedFloat = lambda t: tf.reshape(t, [-1, 1])

castFloat = lambda t: embedFloat(tf.cast(t, tf.float32))

def one_hot(size):
  return lambda t: tf.one_hot(tf.cast(t, tf.int64), size, 1.0, 0.0)

maxAction = 512 # altf4 says 0x017E
actionSpace = 32

maxCharacter = 32 # should be large enough?

maxJumps = 8 # unused

#with 
actionHelper = tfl.makeAffineLayer(maxAction, actionSpace)

def embedAction(t):
  return actionHelper(one_hot(maxAction)(t))

playerEmbedding = {
  "percent" : castFloat,
  "facing" : castFloat,
  "x" : embedFloat,
  "y" : embedFloat,
  "action" : embedAction,
  "action_counter" : castFloat,
  "action_frame" : castFloat,
  "character" : one_hot(maxCharacter),
  "invulnerable" : castFloat,
  "hitlag_frames_left" : castFloat,
  "hitstun_frames_left" : castFloat,
  "jumps_left" : castFloat,
  "charging_smash" : castFloat,
  "on_ground" : castFloat,
  'speed_air_x_self' :  embedFloat,
  'speed_ground_x_self' : embedFloat,
  'speed_y_self' : embedFloat,
  'speed_x_attack' : embedFloat,
  'speed_y_attack' : embedFloat
}

def embedStruct(embedding):
  def f(struct):
    embed = [op(struct[field]) for field, op in embedding.items()]
    return tf.concat(1, embed)
  return f

embedPlayer = embedStruct(playerEmbedding)

maxStage = 64 # overestimate
stageSpace = 32

stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))

gameEmbedding = {
  'player_one' : embedPlayer,
  'player_two' : embedPlayer,

  #('frame', c_uint),
  'stage' : embedStage
}

embedGame = embedStruct(gameEmbedding)
embedded_states = embedGame(input_states)

controllerEmbedding = {
  'buttonA' : castFloat,
  'buttonB' : castFloat,
  'buttonX' : castFloat,
  'buttonY' : castFloat,
  'buttonL' : castFloat,
  'buttonR' : castFloat,
  
  'analogL' : embedFloat,
  'analogR' : embedFloat,
  
  'mainX' : embedFloat,
  'mainY' : embedFloat,
    
  'cX' : embedFloat,
  'cY' : embedFloat
}

embedController = embedStruct(controllerEmbedding)
embedded_controls = embedController(input_controls)

state_actions = tf.concat(1, [embedded_states, embedded_controls])

q1 = tfl.affineLayer(state_actions, 512, tf.tanh)
q = tfl.affineLayer(q1, 1)
q = tf.squeeze(q)

# pre-computed long-term rewards
rewards = tf.placeholder(tf.float32, [None], name='rewards')

qLosses = tf.squared_difference(q, rewards)
qLoss = tf.reduce_sum(qLosses)

trainQ = tf.train.RMSPropOptimizer(0.001).minimize(qLoss)

# see GameState.h for explanations
dyingActions = set([0x0, 0x1, 0x2, 0x4, 0x6, 0x7, 0x8])

def isDying(player):
  return player.action in dyingActions

# from player 2's perspective
def score(state):
  return isDying(state.player_one) - isDying(state.player_two)

def computeRewards(states, discount = 0.99):
  scores = map(score, states)
  return util.scanr1(lambda r1, r2: r1 + discount * r2, scores)
  
def readFile(filename, states=[], controls=[]):
  with open('testRecord0', 'rb') as f:
    for i in range(60 * 60):
      states.append(ssbm.GameMemory())
      f.readinto(states[-1])
      
      controls.append(ssbm.ControllerState())
      f.readinto(controls[-1])
  
  return states, controls

sess = tf.Session()

def computeQLoss(filename):
  states, controls = readFile(filename)
  
  feed_dict = {rewards : computeRewards(states)}
  feedCTypes(ssbm.GameMemory, input_states, states, feed_dict)
  feedCTypes(ssbm.ControllerState, input_controls, controls, feed_dict)
  
  print(sess.run(qLoss, feed_dict))
  sess.run(trainQ, feed_dict)
  print(sess.run(qLoss, feed_dict))

sess.run(tf.initialize_all_variables())
computeQLoss('testRecord0')

