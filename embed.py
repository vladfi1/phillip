import tensorflow as tf
import tf_lib as tfl
import util
import ssbm

embedFloat = lambda t: tf.expand_dims(t, 1)

castFloat = lambda t: embedFloat(tf.cast(t, tf.float32))

def embedStruct(embedding):
  def f(struct):
    embed = []
    for field, op in embedding:
      with tf.name_scope(field):
        embed.append(op(struct[field]))
    return tf.concat(1, embed)
  return f

stickEmbedding = [
  ('x', embedFloat),
  ('y', embedFloat)
]

embedStick = embedStruct(stickEmbedding)

controllerEmbedding = [
  ('button_A', castFloat),
  #('button_B', castFloat),
  #('button_X', castFloat),
  #('button_Y', castFloat),
  #('button_L', castFloat),
  #('button_R', castFloat),

  #('trigger_L', embedFloat),
  #('trigger_R', embedFloat),

  ('stick_MAIN', embedStick),
  #('stick_C', embedStick),
]

embedController = embedStruct(controllerEmbedding)

maxCharacter = 32 # should be large enough?

maxJumps = 8 # unused

maxAction = 512 # altf4 says 0x017E
"""
actionSpace = 32

with tf.variable_scope("embed_action"):
  actionHelper = tfl.makeAffineLayer(maxAction, actionSpace)

def embedAction(t):
  return actionHelper(tfl.one_hot(maxAction)(t))
"""

def rescale(a):
  return lambda x: a * x

playerEmbedding = [
  ("percent", util.compose(rescale(0.01), castFloat)),
  ("facing", embedFloat),
  ("x", util.compose(rescale(0.1), embedFloat)),
  ("y", util.compose(rescale(0.1), embedFloat)),
  ("action_state", tfl.one_hot(maxAction)),
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
  ('speed_y_attack', embedFloat),

  ('controller', embedController)
]

embedPlayer = embedStruct(playerEmbedding)

def embedArray(op, indices=None):
  def f(array):
    #if indices is None:
    #  indices = range(len(array))
    embed = []
    for i in indices:
      with tf.name_scope(str(i)):
        embed.append(op(array[i]))
    return tf.concat(1, embed)
  return f

""" indices is a tensor
def embedArray(op, indices=None):
  def f(array):
    embed = []
    for i, a in enumerate(array):
      with tf.name_scope(str(i)):
        embed.append(op(a))
    packed = tf.pack(embed)
    gathered = tf.gather(indices, packed)
    # can this be done with reshape?
    unpacked = tf.unpack(gathered)
    return tf.concat(1, unpacked)
  return f
"""

"""
maxStage = 64 # overestimate
stageSpace = 32

with tf.variable_scope("embed_stage"):
  stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))
"""

def gameEmbedding(swap):
  players = [1, 0] if swap else [0, 1]
  return [
    ('players', embedArray(embedPlayer, players)),

    #('frame', c_uint),
    # ('stage', embedStage)
  ]

def embedGame(game, swap=False):
  return embedStruct(gameEmbedding(swap))(game)

def embedEnum(enum):
  return tfl.one_hot(len(enum))

simpleControllerEmbedding = [
  ('button', embedEnum(ssbm.SimpleButton)),
  ('stick_MAIN', embedEnum(ssbm.SimpleStick)),
]

embedSimpleController = embedStruct(simpleControllerEmbedding)
#embedded_controls = embedController(train_controls)

action_size = len(ssbm.simpleControllerStates)
embedAction = tfl.one_hot(action_size)
