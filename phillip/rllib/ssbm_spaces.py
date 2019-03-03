import gym
from gym import spaces
import numpy as np
import math
from logging import warning

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

class BoolConv:
  def __init__(self):
    self.space = spaces.Discrete(2)
  def __call__(self, cbool, name=None):
    return int(cbool)

bool_conv = BoolConv()

def clip(x, min_x, max_x):
  return min(max(x, min_x), max_x)

class RealConv:
  def __init__(self, low, high, verbose=True):
    self.low = low
    self.high = high
    self.space = spaces.Box(low, high, ())
    self.verbose = verbose
  
  def __call__(self, x, name=None):
    if math.isnan(x):
      warning("NaN value in %s" % name)
      x = (self.low + self.high) / 2
    if self.low > x or x > self.high:
      if self.verbose:
        warning("%f out of bounds in real space \"%s\"" % (x, name))
      x = clip(x, self.low, self.high)
    return np.array(x)

class DiscreteConv:
  def __init__(self, size, verbose=True):
    self.size = size
    self.space = spaces.Discrete(size)
  
  def __call__(self, x, name=None):
    if 0 > x or x >= self.space.n:
      warning("%d out of bounds in discrete space \"%s\"" % (x, name))
      x = 0
    return x

class StructConv:
  def __init__(self, spec):
    self.spec = spec
    
    self.space = spaces.Tuple([conv.space for _, conv in spec])
  
  def __call__(self, struct, **kwargs):
    return [conv(getattr(struct, name), name=name) for name, conv in self.spec]

class ArrayConv:
  def __init__(self, conv, permutation):
    self.conv = conv
    self.permutation = permutation
    
    self.space = spaces.Tuple([conv.space for _ in permutation])
  
  def __call__(self, array, **kwargs):
    return [self.conv(array[i]) for i in self.permutation]

max_char_id = 32 # should be large enough?

max_action_state = 0x017E
num_action_states = 1 + max_action_state

frame_conv = RealConv(0, 100, 'frame')
speed_conv = RealConv(-10, 10, 'speed') # generally less than 1 in magnitude

player_spec = [
  ('percent', RealConv(0, 999)),
  ('facing', RealConv(-1, 1)),
  ('x', RealConv(-250, 250)),
  ('y', RealConv(-250, 250)),
  ('action_state', DiscreteConv(num_action_states)),
  ('action_frame', RealConv(-1, 100, 'action_frame')),
  ('character', DiscreteConv(max_char_id)),
  ('invulnerable', bool_conv),
  ('hitlag_frames_left', frame_conv),
  ('hitstun_frames_left', RealConv(-6, 100, 'hitstun_frames_left')),
  ('jumps_used', DiscreteConv(8)),
  ('charging_smash', bool_conv),
  ('in_air', bool_conv),
  ('speed_air_x_self', speed_conv),
  ('speed_ground_x_self', speed_conv),
  ('speed_y_self', speed_conv),
  ('speed_x_attack', speed_conv),
  ('speed_y_attack', speed_conv),
  ('shield_size', RealConv(0, 100)),
]

player_conv = StructConv(player_spec)

def make_game_spec(self=0, enemy=1, swap=False):
  players = [self, enemy]
  if swap:
    players.reverse()
  
  return [
    ('players', ArrayConv(player_conv, players)),
    ('stage', DiscreteConv(32)),
  ]

# maps pid to Conv
game_conv_list = [
  StructConv(make_game_spec(swap=False)),
  StructConv(make_game_spec(swap=True)),
]

