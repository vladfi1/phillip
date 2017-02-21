from pad import *

class Fox:
    def __init__(self):
        self.action_list = []
        self.last_action = 0

    def advance(self, state, pad):
        while self.action_list:
            wait, func, args = self.action_list[0]
            if state.frame - self.last_action < wait:
                return
            else:
                self.action_list.pop(0)
                if func is not None:
                    func(*args)
                self.last_action = state.frame
        else:
            # Eventually this will point at some decision-making thing.
            self.shinespam(pad)

    def shinespam(self, pad):
        self.action_list.append((0, pad.tilt_stick, [Stick.MAIN, 0.5, 0.0]))
        self.action_list.append((0, pad.press_button, [Button.B]))
        self.action_list.append((1, pad.release_button, [Button.B]))
        self.action_list.append((0, pad.tilt_stick, [Stick.MAIN, 0.5, 0.5]))
        self.action_list.append((0, pad.press_button, [Button.X]))
        self.action_list.append((1, pad.release_button, [Button.X]))
        self.action_list.append((1, None, []))
