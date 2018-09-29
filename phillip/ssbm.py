"""
Define SSBM types. 
"""

from ctypes import *
from .ctype_util import *
from enum import IntEnum
import struct
import tempfile
import os
#import h5py
import pickle
from . import reward
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
  duration = attr.ib(default=None)
  
  @classmethod
  def init(cls, *args, **kwargs):
    self = cls(*args, **kwargs)
    self.real_controller = self.realController()
    return self
  
  def realController(self):
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

axis_granularity = 3
axis_positions = np.linspace(0, 1, axis_granularity)
diagonal_sticks = list(itertools.product(axis_positions, repeat=2))
diagonal_controllers = [SimpleController.init(*args) for args in itertools.product(SimpleButton, diagonal_sticks)]


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
short_hop = SimpleController.init(button=SimpleButton.Y, duration=2)
short_hop_chain = [short_hop, SimpleController.neutral]

jc_chain = [SimpleController.init(button=SimpleButton.Y, duration=1), SimpleController.init(button=SimpleButton.Z)]

actionTypes = dict(
  old = ActionSet(old_controllers),
  cardinal = ActionSet(cardinal_controllers),
  diagonal = ActionSet(diagonal_controllers),
  custom = ActionSet(custom_controllers),
  short_hop_test = ActionSet([SimpleController.neutral] * 10 + [short_hop_chain]),
  # short_hop = ActionSet(custom_controllers + [short_hop]),
  custom_sh_jc = ActionSet(custom_controllers + [short_hop_chain, jc_chain]),
)

@pretty_struct
class SimpleStateAction(Structure):
  _fields = [
    ('state', GameMemory),
    ('prev_action', c_uint),
    ('action', c_uint),
    ('prob', c_float),
  ]


def prepareStateActions(state_actions):
  """Prepares an experience for pickling.
  
  Args:
    state_actions: A value of type (SimpleStateAction * T), or [SimpleStateAction].
  Returns:
    A structure of numpy arrays of length T.
  """

  vectorized = vectorizeCTypes(SimpleStateAction, state_actions)
  rewards_ = reward.rewards_np(vectorized['state'])
  rewards = reward.computeRewards(state_actions)
  assert(np.max(np.abs(rewards_ - rewards)) < 1e-5)
  
  vectorized['reward'] = rewards
  return vectorized

# TODO: replace pickle with hdf5
def writeStateActions_HDF5(filename, state_actions):
  with tempfile.NamedTemporaryFile(dir=os.path.dirname(filename), delete=False) as tf:
    tf.write(intStruct.pack(len(state_actions)))
    tf.write(state_actions)
    tempname = tf.name
  os.rename(tempname, filename)

def readStateActions_HDF5(filename):
  with open(filename, 'rb') as f:
    size = readInt(f)
    state_actions = (size * SimpleStateAction)()
    f.readinto(state_actions)

    if len(f.read()) > 0:
      raise Exception(filename + " too long!")

    return state_actions
