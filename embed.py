import tensorflow as tf
import tf_lib as tfl
import util
import ssbm

floatType = tf.float32

class FloatEmbedding(object):
  def __init__(self, scale=None, bias=None):
    self.scale = scale
    self.bias = bias
    self.size = 1
  
  def __call__(self, t):
    if t.dtype is not floatType:
      t = tf.cast(t, floatType)
    
    if self.bias:
      t += self.bias
    
    if self.scale:
      t *= self.scale
    
    return tf.expand_dims(t, -1)

embedFloat = FloatEmbedding()

class OneHotEmbedding(object):
  def __init__(self, size):
    self.size = size
  
  def __call__(self, t):
    t = tf.cast(t, tf.int64)
    return tf.one_hot(t, self.size, 1.0, 0.0)

class StructEmbedding(object):
  def __init__(self, embedding):
    self.embedding = embedding
    
    self.size = 0
    for _, op in embedding:
      self.size += op.size
  
  def __call__(self, struct):
    embed = []
    rank = None
    for field, op in self.embedding:
      with tf.name_scope(field):
        t = op(struct[field])
        if rank is None:
          rank = len(t.get_shape())
        else:
          assert(rank == len(t.get_shape()))
        
        embed.append(t)
    return tf.concat(rank-1, embed)

class ArrayEmbedding(object):
  def __init__(self, op, permutation):
    self.op = op
    self.permutation = permutation
    self.size = len(permutation) * op.size
  
  def __call__(self, array):
    embed = []
    rank = None
    for i in self.permutation:
      with tf.name_scope(str(i)):
        t = self.op(array[i])
        if rank is None:
          rank = len(t.get_shape())
        else:
          assert(rank == len(t.get_shape()))
        
        embed.append(t)
    return tf.concat(rank-1, embed)

class FCEmbedding(object):
  def __init__(self, wrapper, size):
    self.wrapper = wrapper
    self.fc = tfl.FCLayer(wrapper.size, size, nl=tfl.leaky_relu)
    self.size = size
  
  def __call__(self, x):
    wrapped = self.wrapper(x)
    y = self.fc(wrapped)
    return y

stickEmbedding = [
  ('x', embedFloat),
  ('y', embedFloat)
]

embedStick = StructEmbedding(stickEmbedding)

# TODO: embed entire controller
controllerEmbedding = [
  ('button_A', embedFloat),
  ('button_B', embedFloat),
  ('button_X', embedFloat),
  ('button_Y', embedFloat),
  ('button_L', embedFloat),
  ('button_R', embedFloat),

  #('trigger_L', embedFloat),
  #('trigger_R', embedFloat),

  ('stick_MAIN', embedStick),
  ('stick_C', embedStick),
]

embedController = StructEmbedding(controllerEmbedding)

maxAction = 0x017E
numActions = 1 + maxAction

maxCharacter = 32 # should be large enough?
maxJumps = 8 # unused

class PlayerEmbedding(StructEmbedding):
  def __init__(self, action_space=32, **kwargs):
    embedAction = OneHotEmbedding(numActions)
    if action_space:
      embedAction = FCEmbedding(embedAction, action_space)

    playerEmbedding = [
      ("percent", FloatEmbedding(scale=0.01)),
      ("facing", embedFloat),
      ("x", FloatEmbedding(scale=0.1)),
      ("y", FloatEmbedding(scale=0.1)),
      ("action_state", embedAction),
      # ("action_counter", embedFloat),
      ("action_frame", FloatEmbedding(scale=0.02)),
      ("character", OneHotEmbedding(maxCharacter)),
      ("invulnerable", embedFloat),
      ("hitlag_frames_left", embedFloat),
      ("hitstun_frames_left", embedFloat),
      ("jumps_used", embedFloat),
      ("charging_smash", embedFloat),
      ("shield_size", embedFloat),
      ("in_air", embedFloat),
      ('speed_air_x_self', embedFloat),
      ('speed_ground_x_self', embedFloat),
      ('speed_y_self', embedFloat),
      ('speed_x_attack', embedFloat),
      ('speed_y_attack', embedFloat),

      #('controller', embedController)
    ]
    
    super(PlayerEmbedding, self).__init__(playerEmbedding)

"""
maxStage = 64 # overestimate
stageSpace = 32

with tf.variable_scope("embed_stage"):
  stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))
"""

class GameEmbedding(StructEmbedding):
  def __init__(self, swap=False, player_space=64, **kwargs):
    embedPlayer = PlayerEmbedding(**kwargs)
    if player_space:
      embedPlayer = FCEmbedding(embedPlayer, player_space)
    
    players = [0, 1]
    if swap: players.reverse()
    
    gameEmbedding = [
      ('players', ArrayEmbedding(embedPlayer, players)),

      #('frame', c_uint),
      #('stage', embedStage)
    ]
    
    super(GameEmbedding, self).__init__(gameEmbedding)

def embedEnum(enum):
  return OneHotEmbedding(len(enum))

simpleAxisEmbedding = OneHotEmbedding(ssbm.axis_granularity)

simpleStickEmbedding = [
  ('x', simpleAxisEmbedding),
  ('y', simpleAxisEmbedding)
]

simpleControllerEmbedding = [
  ('button', embedEnum(ssbm.SimpleButton)),
  ('stick_MAIN', StructEmbedding(simpleStickEmbedding)),
]

# NOTE: this is unused for now - we embed the previous action using a simple one-hot
embedSimpleController = StructEmbedding(simpleControllerEmbedding)

action_size = len(ssbm.simpleControllerStates)
embedAction = OneHotEmbedding(action_size)

