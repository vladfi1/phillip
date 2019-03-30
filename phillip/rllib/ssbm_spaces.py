import copy
import math
from functools import partial
from logging import warning
import numpy as np
from gym import spaces

buttons = ['A', 'B', 'Y', 'L', 'Z']

button_space = spaces.Discrete(len(buttons) + 1)
main_stick_space = spaces.Box(0, 1, [2]) # X and Y axes

c_directions = [(0.5, 0.5), (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)]
c_stick_space = spaces.Discrete(len(c_directions))

controller_space = spaces.Tuple((button_space, main_stick_space, c_stick_space))

def realController(control):
  button, main, c = control
  
  controller = ssbm.RealControllerState()

  if button < len(buttons):
    setattr(controller, 'button_' + buttons[button], True)
  
  controller.stick_MAIN = tuple(main)
  controller.stick_C = c_directions[c]
  
  return controller

class Conv:
  def contains(self, x):
    return True
  
  def make_flat(self, obs):
    array = np.zeros((self.flat_size,))
    self.write(obs, array, 0)
    return array

class BoolConv(Conv):
  flat_size = 2

  def __init__(self, name="BoolConv"):
    self.space = spaces.Discrete(2)
    self.name = name
    self.default_value = 0

  def __call__(self, cbool):
    return int(cbool)
  
  def write(self, b, array, offset):
    array[offset + int(b)] = 1

def clip(x, min_x, max_x):
  return min(max(x, min_x), max_x)

class RealConv(Conv):
  flat_size = 1

  def __init__(self, source, target, verbose=True, default_value=0., name="RealConv"):
    self.source = source
    self.target = target
    m = (target[1] - target[0]) / (source[1] - source[0])
    b = target[0] - source[0] * m
    self.transform = lambda x: m * x + b
    self.space = spaces.Box(min(target), max(target), (), dtype=np.float32)
    self.verbose = verbose
    self.default_value = np.array(default_value)
    self.name = name
    
  def contains(self, x):
    return self.source[0] <= x and x <= self.source[1]

  def _process(self, x):
    if math.isnan(x):
      warning("NaN value in %s" % self.name)
      return self.default_value
    if not self.contains(x):
      if self.verbose:
        warning("%f out of bounds in real space \"%s\"" % (x, self.name))
      x = clip(x, self.space.low, self.space.high)
    return self.transform(x)

  def __call__(self, x):
    return np.array(self._process(x))

  def write(self, x, array, offset):
    array[offset] = self._process(x)

def positive_conv(size, *args, **kwargs):
  return RealConv((0, size), (0, 1), *args, **kwargs)

def symmetric_conv(size, *args, **kwargs):
  return RealConv((-size, size), (-1, 1), *args, **kwargs)

class ExceptionConv(Conv):
  def __init__(self, exceptions, name="ExceptionConv"):
    self.exception_dict = {x: i for i, x in enumerate(exceptions)}
    self.space = spaces.Discrete(len(exceptions)+1)
    self.default_value = len(exceptions)
    self.name = name
    self.flat_size = len(exceptions) + 1
  
  def __call__(self, x):
    if x in self.exception_dict:
      return self.exception_dict[x]
    warning("%s out of bounds in exception space '%s'" % (x, self.name))
    return self.default_value

  def contains(self, x):
    return x in self.exception_dict
    
  def write(self, x, array, offset):
    array[offset + self(x)] = 1

class SumConv(Conv):
  def __init__(self, spec, name="SumConv"):
    self.name = name
    self.convs = [f(name=name + '/' + key) for key, f in spec]
    self.space = spaces.Tuple([conv.space for conv in self.convs])
    self.default_value = tuple(conv.default_value for conv in self.convs)
    self.flat_size = sum(conv.flat_size for conv in self.convs)

  def __call__(self, x):
    return_value = list(self.default_value)
    for i, conv in enumerate(self.convs):
      if conv.contains(x):
        return_value[i] = conv(x)
        return return_value
    
    warning("%s out of bounds in sum space '%s'" % (x, self.name))
    return self.default_value
  
  # this doesn't quite do the same thing as the TupleFlattenProcessor
  def write(self, x, array, offset):
    for conv in self.convs:
      if conv.contains(x):
        conv.write(x, array, offset)
        break
      offset += conv.flat_size

class DiscreteConv(Conv):

  def __init__(self, size, name="DiscreteConv"):
    self.size = size
    self.default_value = size
    self.space = spaces.Discrete(size+1)
    self.name = name
    self.flat_size = size + 1
  
  def __call__(self, x):
    if 0 > x or x >= self.space.n:
      warning("%d out of bounds in discrete space \"%s\"" % (x, self.name))
      x = self.size
    return x
    
  def write(self, x, array, offset):
    array[offset + self(x)] = 1

class StructConv(Conv):
  def __init__(self, spec, name="StructConv"):
    self.spec = [(key, f(name=name + '/' + key)) for key, f in spec]
    self.space = spaces.Tuple([conv.space for _, conv in self.spec])
    self.flat_size = sum(conv.flat_size for _, conv in self.spec)
  
  def __call__(self, struct):
    return [conv(getattr(struct, name)) for name, conv in self.spec]
    
  def write(self, struct, array, offset):
    for name, conv in self.spec:
      conv.write(getattr(struct, name), array, offset)
      offset += conv.flat_size

class ArrayConv:
  def __init__(self, mk_conv, permutation, name="ArrayConv"):
    self.permutation = [(i, mk_conv(name=name + '/' + str(i))) for i in permutation]
    self.space = spaces.Tuple([conv.space for _, conv in self.permutation])
    self.flat_size = sum(conv.flat_size for _, conv in self.permutation)
  
  def __call__(self, array):
    return [conv(array[i]) for i, conv in self.permutation]

  def write(self, raw_array, array, offset):
    for i, conv in self.permutation:
      conv.write(raw_array[i], array, offset)
      offset += conv.flat_size

max_char_id = 32 # should be large enough?

max_action_state = 0x017E
num_action_states = 1 + max_action_state

xy_conv = partial(symmetric_conv, 260)
frame_conv = partial(positive_conv, 180)

# generally less than 1 in magnitude
# side-B reaches 18
speed_conv = partial(symmetric_conv, 20)

hitstun_frames_left_conv = partial(SumConv, [
    ('default', frame_conv),
    ('negative', partial(RealConv, (-5, 0), (-1, 0))),
    ('high_falcon', partial(ExceptionConv, [219, 220])),
])

action_frame_conv = partial(SumConv, [
    ('default', frame_conv),
    ('exception', partial(ExceptionConv, [-1])),
])

player_spec = [
  ('percent', partial(RealConv, (0, 1000), (0, 10))),
  ('facing', partial(symmetric_conv, 1)),
  ('x', xy_conv),
  ('y', xy_conv),
  ('action_state', partial(DiscreteConv, num_action_states)),
  ('action_frame', action_frame_conv),
  ('character', partial(DiscreteConv, max_char_id)),
  ('invulnerable', BoolConv),
  ('hitlag_frames_left', frame_conv),
  ('hitstun_frames_left', hitstun_frames_left_conv),
  ('jumps_used', partial(DiscreteConv, 8)),
  ('charging_smash', BoolConv),
  ('in_air', BoolConv),
  ('speed_air_x_self', speed_conv),
  ('speed_ground_x_self', speed_conv),
  ('speed_y_self', speed_conv),
  ('speed_x_attack', speed_conv),
  ('speed_y_attack', speed_conv),
  ('shield_size', partial(positive_conv, 100)),
]

player_conv = partial(StructConv, player_spec)

def make_game_spec(self=0, enemy=1, swap=False):
  players = [self, enemy]
  if swap:
    players.reverse()
  
  return [
    ('players', partial(ArrayConv, player_conv, players)),
    ('stage', partial(DiscreteConv, 32)),
  ]

# maps pid to Conv
game_conv_list = [
  StructConv(make_game_spec(swap=False), name='game-0'),
  StructConv(make_game_spec(swap=True), name='game-1'),
]

