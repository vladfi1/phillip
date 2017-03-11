import tensorflow as tf
from . import tf_lib as tfl, util, ssbm
from .default import *

floatType = tf.float32

def nullEmbedding(t):
  shape = tf.shape(t)
  shape = tf.concat(0, [shape, [0]])
  return tf.zeros(shape)

nullEmbedding.size = 0

class FloatEmbedding(object):
  def __init__(self, name, scale=None, bias=None, lower=-250., upper=250.):
    self.name = name
    self.scale = scale
    self.bias = bias
    self.lower = lower
    self.upper = upper
    self.size = 1
  
  def __call__(self, t):
    if t.dtype is not floatType:
      t = tf.cast(t, floatType)
    
    if self.bias:
      t += self.bias
    
    if self.scale:
      t *= self.scale
    
    if self.lower:
      t = tf.maximum(t, self.lower)
    
    if self.upper:
      t = tf.minimum(t, self.upper)
    
    return tf.expand_dims(t, -1)

embedFloat = FloatEmbedding("float")

class OneHotEmbedding(object):
  def __init__(self, name, size):
    self.name = name
    self.size = size
  
  def __call__(self, t):
    t = tf.cast(t, tf.int64)
    return tf.one_hot(t, self.size, 1.0, 0.0)

class StructEmbedding(object):
  def __init__(self, name, embedding):
    self.name = name
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
  def __init__(self, name, op, permutation):
    self.name = name
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

class FCEmbedding(Default):
  _options = [
    Option('embed_nl', type=bool, default=True)
  ]
  
  _members = [
    ('nl', tfl.NL)
  ]

  def __init__(self, name, wrapper, size, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.name = name
    
    if not self.embed_nl:
      self.nl = None

    self.wrapper = wrapper
    self.fc = tfl.FCLayer(wrapper.size, size, nl=self.nl)
    self.size = size
  
  def __call__(self, x):
    wrapped = self.wrapper(x)
    y = self.fc(wrapped)
    return y

stickEmbedding = [
  ('x', embedFloat),
  ('y', embedFloat)
]

embedStick = StructEmbedding("stick", stickEmbedding)

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

embedController = StructEmbedding("controller", controllerEmbedding)

maxAction = 0x017E
numActions = 1 + maxAction

maxCharacter = 32 # should be large enough?
maxJumps = 8

class PlayerEmbedding(StructEmbedding, Default):
  _options = [
    Option('action_space', type=int, default=64, help="embed actions in ACTION_SPACE dimensions (deprecated)"),
    Option('xy_scale', type=float, default=0.1, help="scale xy coordinates"),
    Option('shield_scale', type=float, default=0.01),
    Option('speed_scale', type=float, default=0.5),
    Option('omit_char', type=bool, default=False),
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    
    embedAction = OneHotEmbedding("action_state", numActions)
    if self.action_space:
      embedAction = FCEmbedding("action_state", embedAction, self.action_space, **kwargs)
    
    embedXY = FloatEmbedding("xy", scale=self.xy_scale)
    embedSpeed = FloatEmbedding("speed", scale=self.speed_scale)

    playerEmbedding = [
      ("percent", FloatEmbedding("percent", scale=0.01)),
      ("facing", embedFloat),
      ("x", embedXY),
      ("y", embedXY),
      ("action_state", embedAction),
      # ("action_counter", embedFloat),
      ("action_frame", FloatEmbedding("action_frame", scale=0.02)),
      ("character", nullEmbedding if self.omit_char else OneHotEmbedding("character", maxCharacter)),
      ("invulnerable", embedFloat),
      ("hitlag_frames_left", embedFloat),
      ("hitstun_frames_left", embedFloat),
      ("jumps_used", embedFloat),
      ("charging_smash", embedFloat),
      ("shield_size", FloatEmbedding("shield_size", scale=self.shield_scale)),
      ("in_air", embedFloat),
      ('speed_air_x_self', embedSpeed),
      ('speed_ground_x_self', embedSpeed),
      ('speed_y_self', embedSpeed),
      ('speed_x_attack', embedSpeed),
      ('speed_y_attack', embedSpeed),

      #('controller', embedController)
    ]
    
    StructEmbedding.__init__(self, "player", playerEmbedding)

"""
maxStage = 64 # overestimate
stageSpace = 32

with tf.variable_scope("embed_stage"):
  stageHelper = tfl.makeAffineLayer(maxStage, stageSpace)

def embedStage(stage):
  return stageHelper(one_hot(maxStage)(stage))
"""

class GameEmbedding(StructEmbedding, Default):
  _options = [
    Option('player_space', type=int, default=64, help="embed players into PLAYER_SPACE dimensions (deprecated)"),
  ]
  
  _members = [
    ('embedPlayer', PlayerEmbedding)
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    
    if self.player_space:
      self.embedPlayer = FCEmbedding(self.embedPlayer, self.player_space, **kwargs)
    
    players = [0, 1]
    #if self.swap: players.reverse()
    
    gameEmbedding = [
      ('players', ArrayEmbedding("players", self.embedPlayer, players)),

      #('frame', c_uint),
      #('stage', embedStage)
    ]
    
    StructEmbedding.__init__(self, "game", gameEmbedding)

"""
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
"""

