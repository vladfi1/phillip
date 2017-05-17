import tensorflow as tf
from . import tf_lib as tfl, util, ssbm
from .default import *
import math

floatType = tf.float32

def nullEmbedding(t):
  shape = tf.shape(t)
  shape = tf.concat(axis=0, values=[shape, [0]])
  return tf.zeros(shape)

nullEmbedding.size = 0

class FloatEmbedding(object):
  def __init__(self, name, scale=None, bias=None, lower=-10., upper=10.):
    self.name = name
    self.scale = scale
    self.bias = bias
    self.lower = lower
    self.upper = upper
    self.size = 1
  
  def __call__(self, t, **_):
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
  
  def init_extract(self):
    pass
  
  def extract(self, t):
    if self.scale:
      t /= self.scale
    
    if self.bias:
      t -= self.bias
    
    #return t
    return tf.squeeze(t, [-1])
  
  def to_input(self, t):
    return t
  
  def distance(self, predicted, target):
    if target.dtype is not floatType:
      target = tf.cast(target, floatType)
    
    if self.scale:
      target *= self.scale
    
    if self.bias:
      target += self.bias
    
    predicted = tf.squeeze(predicted, [-1])
    return tf.squared_difference(predicted, target)

embedFloat = FloatEmbedding("float")

class OneHotEmbedding(object):
  def __init__(self, name, size):
    self.name = name
    self.size = size
  
  def __call__(self, t, residual=False, **_):
    one_hot = tf.one_hot(t, self.size, 1., 0.)
    
    if residual:
      logits = math.log(self.size * 10) * one_hot
      return logits
    else:
      return one_hot
  
  def to_input(self, logits):
    return tf.nn.softmax(logits)
  
  def extract(self, embedded):
    # TODO: pick a random sample?
    return tf.argmax(t, -1)
  
  def distance(self, embedded, target):
    logprobs = tf.nn.log_softmax(embedded)
    target = self(target)
    return -tfl.batch_dot(logprobs, target)

class StructEmbedding(object):
  def __init__(self, name, embedding):
    self.name = name
    self.embedding = embedding
    
    self.size = 0
    for _, op in embedding:
      self.size += op.size
  
  def __call__(self, struct, **kwargs):
    embed = []
    
    rank = None
    for field, op in self.embedding:
      with tf.name_scope(field):
        t = op(struct[field], **kwargs)
        
        if rank is None:
          rank = len(t.get_shape())
        else:
          assert(rank == len(t.get_shape()))
        
        embed.append(t)
    return tf.concat(axis=rank-1, values=embed)
  
  def to_input(self, embedded):
    rank = len(embedded.get_shape())
    begin = (rank-1) * [0]
    size = (rank-1) * [-1]
    
    inputs = []
    offset = 0
    
    for _, op in self.embedding:
      t = tf.slice(embedded, begin + [offset], size + [op.size])
      inputs.append(op.to_input(t))
      offset += op.size
    
    return tf.concat(axis=rank-1, values=inputs)
  
  def extract(self, embedded):
    rank = len(embedded.get_shape())
    begin (rank-1) * [0]
    size = (rank-1) * [-1]
    
    struct = {}
    offset = 0
    
    for field, op in self.embedding:
      t = tf.slice(embedded, begin + [offset], size + [op.size])
      struct[field] = op.extract(t)
      offset += op.size
    
    return struct
    
  def distance(self, embedded, target):
    rank = len(embedded.get_shape())
    begin = (rank-1) * [0]
    size = (rank-1) * [-1]
    
    distances = {}
    offset = 0
    
    for field, op in self.embedding:
      t = tf.slice(embedded, begin + [offset], size + [op.size])
      distances[field] = op.distance(t, target[field])
      offset += op.size
    
    return distances

class ArrayEmbedding(object):
  def __init__(self, name, op, permutation):
    self.name = name
    self.op = op
    self.permutation = permutation
    self.size = len(permutation) * op.size
  
  def __call__(self, array, **kwargs):
    embed = []
    rank = None
    for i in self.permutation:
      with tf.name_scope(str(i)):
        t = self.op(array[i], **kwargs)
        if rank is None:
          rank = len(t.get_shape())
        else:
          assert(rank == len(t.get_shape()))
        
        embed.append(t)
    return tf.concat(axis=rank-1, values=embed)
  
  def to_input(self, embedded):
    rank = len(embedded.get_shape())
    ts = tf.split(axis=rank-1, num_or_size_splits=len(self.permutation), value=embedded)
    inputs = list(map(self.op.to_input, ts))
    return tf.concat(axis=rank-1, values=inputs)
  
  def extract(self, embedded):
    # a bit suspect here, we can't recreate the original array,
    # only the bits that were embedded. oh well
    array = max(self.permutation) * [None]
    
    ts = tf.split(axis=tf.rank(embedded)-1, num_or_size_splits=len(self.permutation), value=embedded)
    
    for i, t in zip(self.permutation, ts):
      array[i] = self.op.extract(t)
    
    return array

  def distance(self, embedded, target):
    distances = []
  
    ts = tf.split(axis=tf.rank(embedded)-1, num_or_size_splits=len(self.permutation), value=embedded)
    
    for i, t in zip(self.permutation, ts):
      distances.append(self.op.distance(t, target[i]))
    
    return distances

class FCEmbedding(Default):
  _options = [
    Option('embed_nl', type=bool, default=True)
  ]
  
  _members = [
    ('nl', tfl.NL)
  ]

  def __init__(self, name_, wrapper, size, **kwargs):
    Default.__init__(self, **kwargs)
    
    self.name = name_
    
    if not self.embed_nl:
      self.nl = None

    self.wrapper = wrapper
    self.fc = tfl.FCLayer(wrapper.size, size, nl=self.nl)
    self.size = size
  
  def init_extract(self):
    #self.extract = tfl.FCLayer(
    pass

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
    Option('action_space', type=int, default=0, help="embed actions in ACTION_SPACE dimensions (deprecated)"),
    Option('xy_scale', type=float, default=0.1, help="scale xy coordinates"),
    Option('shield_scale', type=float, default=0.01),
    Option('speed_scale', type=float, default=0.5),
    Option('omit_char', type=bool, default=False),
    Option('frame_scale', type=float, default=.1, help="scale frames"),
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    
    embedAction = OneHotEmbedding("action_state", numActions)
    if self.action_space:
      embedAction = FCEmbedding("action_state_fc", embedAction, self.action_space, **kwargs)
    
    embedXY = FloatEmbedding("xy", scale=self.xy_scale)
    embedSpeed = FloatEmbedding("speed", scale=self.speed_scale)
    embedFrame = FloatEmbedding("frame", scale=self.frame_scale)

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
      ("hitlag_frames_left", embedFrame),
      ("hitstun_frames_left", embedFrame),
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
    Option('player_space', type=int, default=0, help="embed players into PLAYER_SPACE dimensions (deprecated)"),
  ]
  
  _members = [
    ('embedPlayer', PlayerEmbedding)
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
    
    if self.player_space:
      self.embedPlayer = FCEmbedding("player_fc", self.embedPlayer, self.player_space, **kwargs)
    
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

