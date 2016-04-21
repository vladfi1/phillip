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
    ('facing', c_bool),
    ('x', c_float),
    ('y', c_float),
    ('z', c_float),
    ('action', c_uint),
    ('action_counter', c_uint),
    ('action_frame', c_float),
    ('character', c_uint),
    ('invulnerable', c_bool),
    ('hitlag_frames_left', c_float),
    ('hitstun_frames_left', c_float),
    ('jumps_left', c_uint),
    ('charging_smash', c_bool),
    ('on_ground', c_bool),
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

class ControllerState(Structure):
  _fields_ = [
    ('buttonA', c_bool),
    ('buttonB', c_bool),
    ('buttonX', c_bool),
    ('buttonY', c_bool),
    ('buttonL', c_bool),
    ('buttonR', c_bool),
  
    ('analogL', c_float),
    ('analogR', c_float),
  
    ('mainX', c_float),
    ('mainY', c_float),
    
    ('cX', c_float),
    ('cY', c_float)
  ]

  __repr__ = toString
  __hash__ = hashStruct
  __eq__ = eqStruct

  def reset(self):
    "Resets controller to neutral position."
    self.buttonA = False
    self.buttonB = False
    self.buttonX = False
    self.buttonY = False
    self.buttonL = False
    self.buttonR = False
    
    self.analogL = 0.0
    self.analogR = 0.0
    
    self.mainX = 0.5
    self.mainY = 0.5
    
    self.cX = 0.5
    self.cY = 0.5

