from enum import IntEnum
import os
import pickle
from .reward import computeRewards
import numpy as np
import itertools
import attr
import recordclass
import typing

class Stick(recordclass.RecordClass):
  x: float = .5
  y: float = .5

  def reset(self):
    self.x = .5
    self.y = .5

Stick.neutral = Stick(.5, .5)

class RealControllerState(recordclass.RecordClass):
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

  stick_MAIN: Stick = Stick.neutral
  stick_C: Stick = Stick.neutral

  """
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
  """

RealControllerState.neutral = RealControllerState(
  button_A = False
  button_B = False
  button_X = False
  button_Y = False
  button_Z = False
  button_L = False
  button_R = False
  button_START = False

  trigger_L = 0.
  trigger_R = 0.

  stick_MAIN = Stick.neutral
  stick_C = Stick.neutral
)

class PlayerMemory(recordclass.RecordClass):
  percent: int
  stock: int
    # 1.0 is right, -1.0 is left
  facing: float
  x: float
  y: float
  z: float
  action_state: int
  action_counter: int
  action_frame: float
  character: int
  invulnerable: bool
  hitlag_frames_left: float
  hitstun_frames_left: float
  jumps_used: int
  charging_smash: bool
  in_air: bool
  speed_air_x_self: float
  speed_ground_x_self: float
  speed_y_self: float
  speed_x_attack: float
  speed_y_attack: float
  shield_size: float

  cursor_x: float
  cursor_y: float

  # NOTE: the sticks here are [-1, 1],
  # not [0, 1] like in pad.py
  controller: RealControllerState

class GameMemory(recordclass.RecordClass):
  players: recordclass.RecordClass("Players", p0=PlayerMemory, p1=PlayerMemory)

  frame: int
  menu: int
  stage: int

  # stage select screen
  sss_cursor_x: float
  sss_cursor_y: float

class SimpleButton(IntEnum):
  NONE = 0
  A = 1
  B = 2
  Z = 3
  Y = 4
  L = 5

neutral_stick = Stick()

class SimpleController(recordclass.RecordClass):
  button: SimpleButton = SimpleButton.NONE
  stick: Stick = neutral_stick
  
  def realController(self):
    kwargs = {'stick_MAIN': self.stick}
    if self.button is not SimpleButton.NONE:
      kwargs["button_%s" % self.button.name] = True
    return RealControllerState(**kwargs)
  
  def banned(self, char):
    if char == 'peach':
      return self.button == SimpleButton.B and self.stick == neutral_stick
    if char in ['sheik', 'zelda']:
      return self.button == SimpleButton.B and self.stick[1] == 0
    return False

SimpleController.neutral = SimpleController()

axis_granularity = 3
axis_positions = np.linspace(0, 1, axis_granularity)
diagonal_sticks = list(itertools.product(axis_positions, repeat=2))
diagonal_controllers = [SimpleController(*args) for args in itertools.product(SimpleButton, diagonal_sticks)]

class SimpleAction:
  def __init__(self, simple_controllers):
    self.simple_controllers = simple_controllers
    self.size = len(simple_controllers)
    self.real_controllers = [None if c is None else c.realController() for c in simple_controllers]
  
  def send(self, index, pad, char=None):
    simple = self.simple_controllers[index]
    if simple is None:
      return
    if simple.banned(char):
      pad.send_controller(RealControllerState.neutral)
    else:
      pad.send_controller(self.real_controllers[index])

old_sticks = [(0.5, 0.5), (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)]
old_controllers = [SimpleController(*args) for args in itertools.product(SimpleButton, old_sticks)]

cardinal_sticks = [(0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1), (0.5, 0.5)]
cardinal_controllers = [SimpleController(*args) for args in itertools.product(SimpleButton, cardinal_sticks)]

tilt_sticks = [(0.4, 0.5), (0.6, 0.5), (0.5, 0.4), (0.5, 0.6)]

custom_controllers = itertools.chain(
  itertools.product([SimpleButton.A, SimpleButton.B], cardinal_sticks),
  itertools.product([SimpleButton.A], tilt_sticks),
  itertools.product([SimpleButton.NONE, SimpleButton.L], diagonal_sticks),
  itertools.product([SimpleButton.Z, SimpleButton.Y], [neutral_stick]),
)
custom_controllers = [SimpleController(*args) for args in custom_controllers]
custom_controllers.append(None)

actionTypes = dict(
  old = SimpleAction(old_controllers),
  cardinal = SimpleAction(cardinal_controllers),
  diagonal = SimpleAction(diagonal_controllers),
  custom = SimpleAction(custom_controllers),
)

class SimpleStateAction(recordclass.RecordClass):
  state: GameMemory
  prev_action: int
  action: int
  prob: float


def prepareStateActions(state_actions):
  """prepares an experience for pickling"""

  vectorized = vectorizeCTypes(SimpleStateAction, state_actions)
  
  rewards = computeRewards(state_actions)
  vectorized['reward'] = rewards
  return vectorized

