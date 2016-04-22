# TODO: move the ctype-generic stuff into a separate file

from ctypes import *

def toString(struct):
  fields = [field + "=" + str(getattr(struct, field)) for (field, _) in struct._fields_]
  return "%s{%s}" % (struct.__class__.__name__, ", ".join(fields))

# TODO: add a named tuple/dict version
def toTuple(struct):
  if isinstance(struct, Structure):
    return tuple(toTuple(getattr(struct, f)) for f, _ in struct._fields_)
  # just a regular ctype
  return struct

def hashStruct(struct):
  return hash(toTuple(struct))

def eqStruct(struct1, struct2):
  return toTuple(struct1) == toTuple(struct2)

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

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

  def reset(self):
    self.x = 0.5
    self.y = 0.5


class SimpleStick(Structure):
  _fields_ = [
    ('up', c_float),
    ('down', c_float),
    ('left', c_float),
    ('right', c_float),
    ('neutral', c_float),
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

  def reset(self):
    self.up = 0
    self.down = 0
    self.left = 0
    self.right = 0
    self.neutral = 1

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

class SimpleButton(Structure):
  _fields_ = [
    ('A', c_float),
    ('none', c_float),
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

  def reset(self):
    self.A = 0
    self.none = 1

class SimpleControllerState(Structure):
  _fields_ = [
    ('buttons', SimpleButton),
    ('stick_MAIN', SimpleStick),
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

  def reset(self):
    "Resets controller to neutral position."
    self.stick_MAIN.reset()
    self.buttons.reset()
