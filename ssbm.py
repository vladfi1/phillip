from ctypes import *
from ctype_util import *
from enum import IntEnum
import struct

class PlayerMemory(Structure):
  _fields_ = [
    ('percent', c_uint),
    ('stock', c_uint),
    # True is right, false is left
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

    ('cursor_x', c_float),
    ('cursor_y', c_float),
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

class GameMemory(Structure):
  _fields_ = [
    ('players', PlayerMemory * 4),

    ('frame', c_uint),
    ('menu', c_uint),
    ('stage', c_uint)
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

class Stick(Structure):
  _fields_ = [
    ('x', c_float),
    ('y', c_float),
  ]

  def __init__(self, x=0.5, y=0.5):
    self.x = x
    self.y = y  
  
  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

  def reset(self):
    self.x = 0.5
    self.y = 0.5


class RealControllerState(Structure):
  _fields_ = [
    ('button_A', c_bool),
    ('button_B', c_bool),
    ('button_X', c_bool),
    ('button_Y', c_bool),
    ('button_L', c_bool),
    ('button_R', c_bool),

    ('trigger_L', c_float),
    ('trigger_R', c_float),

    ('stick_MAIN', Stick),
    ('stick_C', Stick),
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

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

class SimpleButton(IntEnum):
  NONE = 0
  A = 1

class SimpleStick(IntEnum):
  NEUTRAL = 0
  UP = 1
  DOWN = 2
  LEFT = 3
  RIGHT = 4

SimpleStick.UP.stick = Stick(0.5, 1)
SimpleStick.DOWN.stick = Stick(0.5, 0)
SimpleStick.LEFT.stick = Stick(0, 0.5)
SimpleStick.RIGHT.stick = Stick(1, 0.5)
SimpleStick.NEUTRAL.stick = Stick(0.5, 0.5)

@pretty_struct
class SimpleControllerState(Structure):
  _fields = [
    ('button', SimpleButton),
    ('stick_MAIN', SimpleStick),
  ]
  
  def __init__(self, button=SimpleButton.NONE, stick_MAIN=SimpleStick.NEUTRAL):
    self.button = button
    self.stick_MAIN = stick_MAIN
  
  def reset(self):
    self.button = SimpleButton.NONE
    self.main = SimpleStick.NEUTRAL
  
  def realController(self):
    controller = RealControllerState()
    controller.button_A = self.button == SimpleButton.A
    #controller.button_B = self.button == SimpleButton.B
    
    controller.stick_MAIN = SimpleStick(self.stick_MAIN).stick
    return controller
  
simpleControllerStates = SimpleControllerState.allValues()

intStruct = struct.Struct('i')

def readInt(f):
  return intStruct.unpack(f.read(4))[0]

def writeStateActions(filename, data):
  with open(filename, 'wb') as f:
    f.write(intStruct.pack(len(data)))
    
    for state, control in data:
      f.write(state)
      f.write(control)

def readStateActions(filename, stateActions = None):
  if stateActions is None:
    stateActions = []

  with open(filename, 'rb') as f:
    size = readInt(f)
    
    for i in range(size):
      state = GameMemory()
      f.readinto(state)

      control = SimpleControllerState()
      f.readinto(control)
      
      stateActions.append((state, control))

    assert(len(f.read()) == 0)

  return stateActions

