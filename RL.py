import tensorflow as tf
import ssbm
import ctypes
import tf_lib as tfl
import util

with tf.name_scope('train'):
  train_states = tfl.inputCType(ssbm.GameMemory, [None], "states")

  # player 2's controls
  train_controls = tfl.inputCType(ssbm.ControllerState, [None], "controls")

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
embedded_states = embedGame(train_states)
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
embedded_controls = embedController(train_controls)
control_size = embedded_controls.get_shape()[-1].value
assert(control_size == 12)

with tf.variable_scope("q_net"):
  q1 = tfl.makeAffineLayer(state_size + control_size, 512, tf.tanh)
  q2 = tfl.makeAffineLayer(512, 1)

def q(states, controls):
  state_actions = tf.concat(1, [states, controls])
  return tf.squeeze(q2(q1(state_actions)), name='q')

# pre-computed long-term rewards
rewards = tf.placeholder(tf.float32, [None], name='rewards')

with tf.name_scope('trainQ'):
  qPredictions = q(embedded_states, embedded_controls)

  qLosses = tf.squared_difference(qPredictions, rewards)
  qLoss = tf.reduce_mean(qLosses)

  #trainQ = tf.train.RMSPropOptimizer(0.0001).minimize(qLoss)
  trainQ = tf.train.AdamOptimizer().minimize(qLoss)

with tf.variable_scope("actor"):
  layers = [state_size, 64, control_size]
  # all controls are in [0, 1]
  nls = [tf.tanh] * (len(layers) - 2) + [tf.sigmoid]
  
  zip_layers = zip(layers[:-1], layers[1:])
  
  applyLayers = [tfl.makeAffineLayer(prev, next, nl) for (prev, next), nl in zip(zip_layers, nls)]

def applyActor(state):
  for f in applyLayers:
    state = f(state)
  return state

actor_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
#print(actor_variables)

with tf.name_scope("actorQ"):
  actions = applyActor(embedded_states)
  actorQ = tf.reduce_mean(q(embedded_states, actions))

#trainActor = tf.train.RMSPropOptimizer(0.001).minimize(-actorQ)
# FIXME: is this the right sign?
#trainActor = tf.train.RMSPropOptimizer(0.0001).minimize(-actorQ, var_list=actor_variables)
trainActor = tf.train.AdamOptimizer().minimize(-actorQ, var_list=actor_variables)

def deepMap(f, obj):
  if isinstance(obj, dict):
    return {k : deepMap(f, v) for k, v in obj.items()}
  if isinstance(obj, list):
    return [deepMap(f, x) for x in obj]
  return f(obj)

with tf.name_scope('predict'):
  predict_input_state = tfl.inputCType(ssbm.GameMemory, [], "state")
  reshaped = deepMap(lambda t: tf.reshape(t, [1]), predict_input_state)
  embedded_state = embedGame(reshaped)

  predict_actions = applyActor(embedded_state)
  predict_action = tf.squeeze(predict_actions, name="action")
  predictQ = q(embedded_state, predict_actions)
    
  #split = tf.split(0, 12, embedded_action, name='action')

sess = tf.Session()

#summaryWriter = tf.train.SummaryWriter('logs/', sess.graph)
#summaryWriter.flush()

saver = tf.train.Saver(tf.all_variables())

# see https://docs.google.com/spreadsheets/d/1JX2w-r2fuvWuNgGb6D3Cs4wHQKLFegZe2jhbBuIhCG8/edit#gid=13
dyingActions = set(range(0xA))

def isDying(player):
  return player.action in dyingActions

# players tend to be dead for many frames in a row
# here we prune a all but the first frame of the death
def processDeaths(deaths):
  return util.zipWith(lambda prev, next: (not prev) and next, [False] + deaths[:-1] , deaths)

# from player 2's perspective
def computeRewards(states, discount = 0.99):
  kills = [isDying(state.players[0]) for state in states]
  deaths = [isDying(state.players[1]) for state in states]
  
  kills = processDeaths(kills)
  deaths = processDeaths(deaths)
  
  scores = util.zipWith(lambda x, y: x - y, kills, deaths)
  
  lastQ = sess.run(predictQ, tfl.feedCType(ssbm.GameMemory, 'predict/state', states[-1]))
  #lastQ = sess.run(qPredictions, feedCTypes(ssbm.GameMemory, predict_input_state, states[-1:]))
  
  return util.scanr(lambda r1, r2: r1 + discount * r2, lastQ, scores[1:-1])
  
def readFile(filename, states=None, controls=None):
  if states is None:
    states = []
  if controls is None:
    controls = []
  
  with open(filename, 'rb') as f:
    for i in range(60 * 60):
      states.append(ssbm.GameMemory())
      f.readinto(states[-1])
      
      controls.append(ssbm.ControllerState())
      f.readinto(controls[-1])
    
    # should be zero
    # print(len(f.read()))
  
  return states, controls

def train(filename, steps=1):
  states, controls = readFile(filename)
  
  feed_dict = {rewards : computeRewards(states)}
  tfl.feedCTypes(ssbm.GameMemory, 'train/states', states[:-1], feed_dict)
  tfl.feedCTypes(ssbm.ControllerState, 'train/controls', controls[:-1], feed_dict)
  
  # FIXME: we feed the inputs in on each iteration, which might be inefficient.
  for _ in range(steps):
    #sess.run([trainQ, trainActor], feed_dict)
    sess.run(trainQ, feed_dict)
    sess.run(trainActor, feed_dict)
  print(sess.run([qLoss, actorQ], feed_dict))

def save(filename='saves/simpleDQN'):
  saver.save(sess, filename)

def restore(filename='saves/simpleDQN'):
  saver.restore(sess, filename)

def writeGraph():
  graph_def = tf.python.client.graph_util.convert_variables_to_constants(sess, sess.graph_def, ['predict/action'])
  tf.train.write_graph(graph_def, 'models/', 'simpleDQN.pb', as_text=False)

def init():
  sess.run(tf.initialize_all_variables())
#train('testRecord0')

#saver.restore(sess, 'saves/simpleDQN')
#writeGraph()

