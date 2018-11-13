"""
Define SSBM types. 
"""

from enum import IntEnum
import struct
import tempfile
import os
#import h5py
import pickle
from . import reward, fields
import numpy as np
import itertools
import attr
from typing import Tuple

@attr.s(auto_attribs=True)
class Stick:
  x: float = 0.5
  y: float = 0.5

  def reset(self):
    self.x = 0.5
    self.y = 0.5
  
  @classmethod
  def polar(cls, theta, r=1.):
    r /= 2.
    return cls(x=0.5+r*np.cos(theta), y=0.5+r*np.sin(theta))

Stick.neutral = Stick()

@attr.s(auto_attribs=True)
class RealControllerState:
  button_A: bool = False
  button_B: bool = False
  button_X: bool = False
  button_Y: bool = False
  button_Z: bool = False
  button_L: bool = False
  button_R: bool = False
  button_START: bool = False

  trigger_L: float = 0.
  trigger_R: float = 0.

  stick_MAIN: Stick = attr.Factory(Stick)
  stick_C: Stick = attr.Factory(Stick)
  
RealControllerState.neutral = RealControllerState()

@attr.s(auto_attribs=True)
class PlayerMemory:
  percent: int = 0
  stock: int = 0
  # 1.0 is right, -1.0 is left
  facing: float = 1
  x: float = 0.
  y: float = 0.
  z: float = 0.
  action_state: int = 0
  action_counter: int = 0
  action_frame: float = 0.
  character: int = 0
  invulnerable: bool = False
  hitlag_frames_left: float = 0.
  hitstun_frames_left: float = 0.
  jumps_used: int = 0
  charging_smash: bool = False
  in_air: bool = False
  speed_air_x_self: float = 0.
  speed_ground_x_self: float = 0.
  speed_y_self: float = 0.
  speed_x_attack: float = 0.
  speed_y_attack: float = 0.
  shield_size: float = 0.

  cursor_x: float = 0.
  cursor_y: float = 0.

  # NOTE: the sticks here are [-1, 1],
  # not [0, 1] like in pad.py
  controller: RealControllerState = attr.Factory(RealControllerState)

@attr.s(auto_attribs=True)
class GameMemory:
  players: Tuple[PlayerMemory, PlayerMemory] = fields.tupleFactory(PlayerMemory, PlayerMemory)
  frame: int = 0
  menu: int = 0
  stage: int = 0

  # stage select screen
  sss_cursor_x: float = 0.
  sss_cursor_y: float = 0.


class SimpleButton(IntEnum):
  NONE = 0
  A = 1
  B = 2
  Z = 3
  Y = 4
  L = 5

@attr.s(auto_attribs=True)
class SimpleController:
  button: SimpleButton = SimpleButton.NONE
  stick: Stick = attr.Factory(Stick)
  duration: int = None
  
  @classmethod
  def init(cls, *args, **kwargs):
    self = cls(*args, **kwargs)
    self.real_controller = self.realController()
    return self
  
  def realController(self):
    controller = RealControllerState()
    if self.button is not SimpleButton.NONE:
      setattr(controller, "button_%s" % self.button.name, True)

    assert(isinstance(self.stick, Stick))
    controller.stick_MAIN = self.stick
    return controller
  
  def banned(self, char):
    if char == 'peach':
      return self.button == SimpleButton.B and self.stick == Stick.neutral
    if char in ['sheik', 'zelda']:
      return self.button == SimpleButton.B and self.stick.y == 0
    if char == 'fox':
      return self.button == SimpleButton.B and self.stick == Stick.neutral
    return False
  
  def send(self, pad, char):
    if self.banned(char):
      pad.send_controller(RealControllerState.neutral)
    else:
      pad.send_controller(self.real_controller)

SimpleController.neutral = SimpleController.init()


class RepeatController(object):
  duration = None

  def send(self, pad, char):
    pass

repeat_controller = RepeatController()

class ActionChain(object):
  """
  A list of actions, each with a duration, and the last duration must be None.
  
  TODO: Come up with a better system?
  """

  def __init__(self, action_list, act_every):
    self.actions = []
    for action in action_list:
      if action.duration:
        self.actions += [action] * action.duration
      else:
        self.actions += [action] * (act_every - len(self.actions))
    assert len(self.actions) == act_every
    self.index = 0

  def act(self, pad, char):
    self.actions[self.index].send(pad, char)
    self.index += 1
  
  def done(self):
    return self.index == len(self.actions)


class ActionSet(object):
  def __init__(self, actions):
    self.actions = list(map(lambda obj: obj if isinstance(obj, list) else [obj], actions))
    self.size = len(actions)
  
  def choose(self, index, act_every):
    return ActionChain(self.actions[index], act_every)

def makeSticks(*pairs):
  return [Stick(*p) for p in pairs]

old_sticks = makeSticks((0.5, 0.5), (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5))
old_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, old_sticks)]

axis_granularity = 3
axis_positions = np.linspace(0, 1, axis_granularity)
diagonal_sticks = makeSticks(*itertools.product(axis_positions, repeat=2))
diagonal_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, diagonal_sticks)]

cardinal_sticks = makeSticks((0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1), (0.5, 0.5))
cardinal_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, cardinal_sticks)]

tilt_sticks = makeSticks((0.4, 0.5), (0.6, 0.5), (0.5, 0.4), (0.5, 0.6))

custom_controllers = itertools.chain(
  itertools.product([SimpleButton.A, SimpleButton.B], cardinal_sticks),
  itertools.product([SimpleButton.A], tilt_sticks),
  itertools.product([SimpleButton.NONE, SimpleButton.L], diagonal_sticks),
  itertools.product([SimpleButton.Z, SimpleButton.Y], [Stick.neutral]),
)
custom_controllers = [SimpleController.init(*args) for args in custom_controllers]
custom_controllers.append(repeat_controller)

# allows fox, sheik, samus, etc to short hop with act_every=3
short_hop = SimpleController.init(button=SimpleButton.Y, duration=2)
short_hop_chain = [short_hop, SimpleController.neutral]

# this is technically no longer needed because of sh2
jc_chain = [SimpleController.init(button=SimpleButton.Y, duration=1), SimpleController.init(button=SimpleButton.Z)]

# better sh that also allows jc grab and upsmash at act_every 3
sh2_chain = [
  SimpleController.init(duration=2),
  SimpleController.init(button=SimpleButton.Y),
]

fox_wd_chain_left = [
  SimpleController.init(button=SimpleButton.Y, duration=3),
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

@attr.s(auto_attribs=True)
class InputStateAction:
  state: GameMemory
  prev_action: int

@attr.s(auto_attribs=True)
class OutputStateAction:
  state: GameMemory
  prev_action: int
  action: int
  prob: float


