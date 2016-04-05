from ctypes import *

class PlayerMemory(Structure):
  _fields_ = [
    ('percent', c_uint),
    ('stock', c_uint),
    # True is right, false is left
    ('facing', c_uint),
    ('x', c_float),
    ('y', c_float),
    ('action', c_uint),
    ('action_counter', c_uint),
    ('action_frame', c_uint),
    ('character', c_uint),
    ('invulnerable', c_bool),
    ('hitlag_frames_left', c_uint),
    ('hitstun_frames_left', c_uint),
    ('jumps_left', c_uint),
    ('charging_smash', c_bool),
    ('on_ground', c_bool),
    ('speed_air_x_self', c_float),
    ('speed_ground_x_self', c_float),
    ('speed_y_self', c_float),
    ('speed_x_attack', c_float),
    ('speed_y_attack', c_float)
  ]

class GameMemory(Structure):
  _fields_ = [
    ('player_one', PlayerMemory),
    ('player_two', PlayerMemory),

    #Character select screen pointer for player 2
    ('player_two_pointer_x', c_float),
    ('player_two_pointer_y', c_float),

    ('frame', c_uint),
    ('menu_state', c_uint),
    ('stage', c_uint)
  ]

