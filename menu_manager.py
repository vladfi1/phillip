import math

from pad import *

def pushButton(button):
  return lambda pad: pad.push_button(button)

def releaseButton(button):
  return lambda pad: pad.release_button(button)

class MenuManager:
    def __init__(self):
        self.selected_fox = False

    def pick_fox(self, state, pad):
        if self.selected_fox:
            # Release buttons and lazilly rotate the c stick.
            pad.release_button(Button.A)
            pad.tilt_stick(Stick.MAIN, 0.5, 0.5)
            angle = (state.frame % 240) / 240.0 * 2 * math.pi
            #pad.tilt_stick(Stick.C, 0.4 * math.cos(angle) + 0.5, 0.4 * math.sin(angle) + 0.5)
            #pad.tilt_stick(Stick.C, 0.5, 1)
        else:
            # Go to fox and press A
            target_x = -23.5
            target_y = 11.5
            dx = target_x - state.players[1].cursor_x
            dy = target_y - state.players[1].cursor_y
            mag = math.sqrt(dx * dx + dy * dy)
            if mag < 0.3:
                pad.press_button(Button.A)
                self.selected_fox = True
                pad.tilt_stick(Stick.MAIN, 0.5, 0.5)
            else:
                pad.tilt_stick(Stick.MAIN, 0.5 * (dx / mag) + 0.5, 0.5 * (dy / mag) + 0.5)

    def press_start_lots(self, state, pad):
        if state.frame % 2 == 0:
            pad.press_button(Button.START)
        else:
            pad.release_button(Button.START)
