import math

from pad import *

def pushButton(button):
  return lambda state, pad: pad.push_button(button)

def releaseButton(button):
  return lambda state, pad: pad.release_button(button)

characters = dict(
  fox = (-23.5, 11.5),
  falcon = (18, 18),
  roy = (18, 5),
  marth = (11, 5),
  zelda = (11, 11),
)

class MenuManager:
    def __init__(self, target, pid=1):
        self.pid = pid
        self.x, self.y = target
        self.reached = False

    def move(self, state, pad):
        if self.reached:
            # Release buttons
            pad.release_button(Button.A)
            pad.tilt_stick(Stick.MAIN, 0.5, 0.5)
        else:
            player = state.players[self.pid]
            dx = self.x - player.cursor_x
            dy = self.y - player.cursor_y
            mag = math.sqrt(dx * dx + dy * dy)
            if mag < 0.3:
                pad.press_button(Button.A)
                self.reached = True
                pad.tilt_stick(Stick.MAIN, 0.5, 0.5)
            else:
                pad.tilt_stick(Stick.MAIN, 0.5 * (dx / (mag+1)) + 0.5, 0.5 * (dy / (mag+1)) + 0.5)

    def press_start_lots(self, state, pad):
        if state.frame % 2 == 0:
            pad.press_button(Button.START)
        else:
            pad.release_button(Button.START)
