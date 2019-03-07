"""
Define SSBM types. 
"""

from ctypes import *
from .ctype_util import *
from enum import IntEnum
import struct
import tempfile
import os
import pickle
import numpy as np
import itertools
import attr

@pretty_struct
class Stick(Structure):
  _fields = [
    ('x', c_float),
    ('y', c_float),
  ]

  def __init__(self, x=0.5, y=0.5):
    self.x = x
    self.y = y

  def reset(self):
    self.x = 0.5
    self.y = 0.5
  
  @classmethod
  def polar(cls, theta, r=1.):
    r /= 2.
    return cls(x=0.5+r*np.cos(theta), y=0.5+r*np.sin(theta))

@pretty_struct
class RealControllerState(Structure):
  _fields = [
    ('button_A', c_bool),
    ('button_B', c_bool),
    ('button_X', c_bool),
    ('button_Y', c_bool),
    ('button_Z', c_bool),
    ('button_L', c_bool),
    ('button_R', c_bool),
    ('button_START', c_bool),

    ('trigger_L', c_float),
    ('trigger_R', c_float),

    ('stick_MAIN', Stick),
    ('stick_C', Stick),
  ]

  def __init__(self):
    self.reset()

  def reset(self):
    "Resets controller to neutral position."
    self.button_A = False
    self.button_B = False
    self.button_X = False
    self.button_Y = False
    self.button_L = False
    self.button_R = False

    self.analog_L = 0.0
    self.analog_R = 0.0

    self.stick_MAIN.reset()
    self.stick_C.reset()
  
RealControllerState.neutral = RealControllerState()

@pretty_struct
class PlayerMemory(Structure):
  _fields = [
    ('percent', c_uint),
    ('stock', c_uint),
    # 1.0 is right, -1.0 is left
    ('facing', c_float),
    ('x', c_float),
    ('y', c_float),
    ('z', c_float),
    ('action_state', c_uint),
    ('action_counter', c_uint),
    ('action_frame', c_float),
    ('character', c_uint),
    ('invulnerable', c_bool),
    ('hitlag_frames_left', c_float),
    ('hitstun_frames_left', c_float),
    ('jumps_used', c_uint),
    ('charging_smash', c_bool),
    ('in_air', c_bool),
    ('speed_air_x_self', c_float),
    ('speed_ground_x_self', c_float),
    ('speed_y_self', c_float),
    ('speed_x_attack', c_float),
    ('speed_y_attack', c_float),
    ('shield_size', c_float),

    ('cursor_x', c_float),
    ('cursor_y', c_float),

    # NOTE: the sticks here are [-1, 1],
    # not [0, 1] like in pad.py
    ('controller', RealControllerState)
  ]

@pretty_struct
class GameMemory(Structure):
  _fields = [
    ('players', PlayerMemory * 2),

    ('frame', c_uint),
    ('menu', c_uint),
    ('stage', c_uint),
    
    # stage select screen
    ('sss_cursor_x', c_float),
    ('sss_cursor_y', c_float),
  ]

class SimpleButton(IntEnum):
  NONE = 0
  A = 1
  B = 2
  Z = 3
  Y = 4
  L = 5

neutral_stick = (0.5, 0.5)

@attr.s
class SimpleController(object):
  button = attr.ib(default=SimpleButton.NONE)
  stick = attr.ib(default=neutral_stick)
  
  @classmethod
  def init(cls, *args, **kwargs):
    self = cls(*args, **kwargs)
    self.real_controller = self.make_real_controller()
    return self
  
  def make_real_controller(self):
    controller = RealControllerState()
    if self.button is not SimpleButton.NONE:
      setattr(controller, "button_%s" % self.button.name, True)

    controller.stick_MAIN = self.stick
    return controller
  
  def banned(self, char):
    if char == 'peach':
      return self.button == SimpleButton.B and self.stick == neutral_stick
    if char in ['sheik', 'zelda']:
      return self.button == SimpleButton.B and self.stick[1] == 0
    if char == 'fox':
      return self.button == SimpleButton.B and self.stick == neutral_stick
    return False

  def get_real_controller(self, char):
    return RealControllerState.neutral if self.banned(char) else self.real_controller
  
  def send(self, pad, char):
    pad.send_controller(self.get_real_controller(char))

SimpleController.neutral = SimpleController.init()


class RepeatController(object):

  def get_real_controller(self, char):
    return None

  def send(self, pad, char):
    pass

repeat_controller = RepeatController()

axis_granularity = 3
axis_positions = np.linspace(0, 1, axis_granularity)
diagonal_sticks = list(itertools.product(axis_positions, repeat=2))
diagonal_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, diagonal_sticks)]


def make_action_chain(action_list, act_every):
  extra_no_ops = act_every - len(action_list)
  assert(extra_no_ops >= 0)  # maybe this is ok?
  if extra_no_ops > 0:
    return action_list + [repeat_controller] * extra_no_ops
  return action_list

class ActionSet(object):
  def __init__(self, actions):
    self.actions = [obj if isinstance(obj, list) else [obj] for obj in actions]
    self.size = len(actions)
  
  def get_action_chains(self, act_every):
    return [make_action_chain(chain, act_every) for chain in self.actions]
  
  def choose(self, index, act_every):
    return ActionChain(self.actions[index], act_every)

old_sticks = [(0.5, 0.5), (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)]
old_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, old_sticks)]

cardinal_sticks = [(0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1), (0.5, 0.5)]
cardinal_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, cardinal_sticks)]

tilt_sticks = [(0.4, 0.5), (0.6, 0.5), (0.5, 0.4), (0.5, 0.6)]

custom_controllers = itertools.chain(
  itertools.product([SimpleButton.A, SimpleButton.B], cardinal_sticks),
  itertools.product([SimpleButton.A], tilt_sticks),
  itertools.product([SimpleButton.NONE, SimpleButton.L], diagonal_sticks),
  itertools.product([SimpleButton.Z, SimpleButton.Y], [neutral_stick]),
)
custom_controllers = [SimpleController.init(*args) for args in custom_controllers]
custom_controllers.append(repeat_controller)

# allows fox, sheik, samus, etc to short hop with act_every=3
short_hop = SimpleController.init(button=SimpleButton.Y)
short_hop_chain = [short_hop, repeat_controller, SimpleController.neutral]

# this is technically no longer needed because of sh2
jc_chain = [SimpleController.init(button=SimpleButton.Y), SimpleController.init(button=SimpleButton.Z)]

# better sh that also allows jc grab and upsmash at act_every 3
sh2_chain = [
  SimpleController.neutral,
  repeat_controller,
  SimpleController.init(button=SimpleButton.Y),
]

fox_wd_chain_left = [
  SimpleController.init(button=SimpleButton.Y),
  repeat_controller,
  repeat_controller,
  SimpleController.init(button=SimpleButton.L, stick=Stick.polar(-7/8 * np.pi))
]

wd_left = SimpleController.init(button=SimpleButton.L, stick=Stick.polar(-7/8 * np.pi))
wd_right = SimpleController.init(button=SimpleButton.L, stick=Stick.polar(-1/8 * np.pi))
wd_both = [wd_left, wd_right]

actionTypes = dict(
  old = ActionSet(old_controllers),
  cardinal = ActionSet(cardinal_controllers),
  diagonal = ActionSet(diagonal_controllers),
  custom = ActionSet(custom_controllers),
  short_hop_test = ActionSet([SimpleController.neutral] * 10 + [short_hop_chain]),
  # short_hop = ActionSet(custom_controllers + [short_hop]),
  custom_sh_jc = ActionSet(custom_controllers + [short_hop_chain, jc_chain]),
  fox_wd_test = ActionSet([SimpleController.neutral] * 10 + [fox_wd_chain_left]),
  custom_sh2_wd = ActionSet(custom_controllers + [sh2_chain] + wd_both),
)

