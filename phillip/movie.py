from .pad import *

def pushButton(button):
  return lambda pad: pad.press_button(button)

def releaseButton(button):
  return lambda pad: pad.release_button(button)

def tiltStick(stick, x, y):
  return lambda pad: pad.tilt_stick(stick, x, y)

neutral = tiltStick(Stick.MAIN, 0.5, 0.5)
left = tiltStick(Stick.MAIN, 0, 0.5)
down = tiltStick(Stick.MAIN, 0.5, 0)
up = tiltStick(Stick.MAIN, 0.5, 1)
right = tiltStick(Stick.MAIN, 1, 0.5)

endless_netplay = [
  # time
  (0, left),
  
  # infinite time
  (26, down),
  (19, left),
  (25, neutral),
  
  # exit settings
  (1, pushButton(Button.START)),
  (1, releaseButton(Button.START)),
  
  # enter stage select
  (28, pushButton(Button.START)),
  (1, releaseButton(Button.START)),
  
  (10, neutral)
]

stages = dict(
  battlefield = [
    (0, up),
    (2, neutral),
    
    #(60 * 60, neutral),
    
    # start game
    (20, pushButton(Button.START)),
    (1, releaseButton(Button.START)),
  ],
  
  final_destination = [
    (0, tiltStick(Stick.MAIN, 1, 0.8)),
    (5, neutral),
    
    #(60 * 60, neutral),
    
    # start game
    (20, pushButton(Button.START)),
    (1, releaseButton(Button.START)),
  ]
)

class Movie:
  def __init__(self, actions, pad):
    self.actions = actions
    self.frame = 0
    self.index = 0
    self.pad = pad
  
  def move(self, state):
    if not self.done():
      frame, action = self.actions[self.index]
      if self.frame == frame:
        action(self.pad)
        self.index += 1
        self.frame = 0
      else:
       self.frame += 1
  
  def done(self):
    return self.index == len(self.actions)
