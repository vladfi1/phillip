import math

from .pad import *

characters = dict(
  fox = (-23.5, 11.5),
  falco = (-30, 11),
  falcon = (18, 18),
  roy = (18, 5),
  marth = (11, 5),
  zelda = (11, 11),
  sheik = (11, 11),
  mewtwo = (-2, 5),
  luigi = (-16, 18),
  puff = (-10, 5),
  kirby = (-2, 11),
  peach = (-2, 18),
  ganon = (23, 18),
  samus = (3, 11),
  bowser = (-9, 19),
  yoshi = (5, 18),
  dk = (11, 18),
)

settings = (0, 24)

staged = dict(
  final_destination = (0, 0),
)

def locateCSSCursor(pid):
  def locate(state):
    player = state.players[pid]
    return (player.cursor_x, player.cursor_y)
  return locate

def locateSSSCursor(state):
  return (state.sss_cursor_x, state.sss_cursor_y)

class MoveTo:
  def __init__(self, target, locator, pad, relative=False):
    self.target = target
    self.locator = locator
    self.pad = pad
    self.reached = False
    self.relative = relative
    
  def move(self, state):
    x, y = self.locator(state)
    
    if self.relative:
      self.target[0] += x
      self.target[1] += y
      self.relative = False
    
    dx = self.target[0] - x
    dy = self.target[1] - y
    mag = math.sqrt(dx * dx + dy * dy)
    if mag < 0.5:
      self.pad.tilt_stick(Stick.MAIN, 0.5, 0.5)
      self.reached = True
    else:
      self.pad.tilt_stick(Stick.MAIN, 0.4 * (dx / (mag+2)) + 0.5, 0.4 * (dy / (mag+2)) + 0.5)
      self.reached = False

  def done(self):
    return self.reached

class Wait:
  def __init__(self, frames):
    self.frames = frames
  
  def done(self):
    return self.frames == 0
  
  def move(self, state):
    self.frames -= 1

class Action:
  def __init__(self, action, pad):
    self.action = action
    self.pad = pad
    self.acted = False
  
  def done(self):
    return self.acted
  
  def move(self, state):
    self.action(self.pad)
    self.acted = True

class Sequential:
  def __init__(self, *actions):
    self.actions = actions
    self.index = 0
  
  def move(self, state):
    if not self.done():
      action = self.actions[self.index]
      if action.done():
        self.index += 1
      else:
        action.move(state)

  def done(self):
    return self.index == len(self.actions)

class Parallel:
  def __init__(self, *actions):
    self.actions = actions
    self.complete = False
  
  def move(self, state):
    self.complete = True
    for action in self.actions:
      if not action.done():
        action.move(state)
        self.complete = False
  
  def done(self):
    return self.complete

