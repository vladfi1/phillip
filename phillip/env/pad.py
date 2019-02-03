import enum
import os
from threading import Thread
from . import util

@enum.unique
class Button(enum.Enum):
    A = 0
    B = 1
    X = 2
    Y = 3
    Z = 4
    START = 5
    L = 6
    R = 7
    D_UP = 8
    D_DOWN = 9
    D_LEFT = 10
    D_RIGHT = 11

@enum.unique
class Trigger(enum.Enum):
    L = 0
    R = 1

@enum.unique
class Stick(enum.Enum):
    MAIN = 0
    C = 1

class Pad:
    """Writes out controller inputs."""
    def __init__(self, path, tcp=False):
        """Opens the fifo. Blocks until the other end is listening.
        Args:
          path: Path to pipe file.
          tcp: Whether to use zmq over tcp or a fifo. If true, the pipe file
            is simply a text file containing the port number. The port will
            be a hash of the path.
        """
        self.tcp = tcp
        if tcp:
          import zmq
          context = zmq.Context()
          port = util.port(path)
          
          with open(path, 'w') as f:
            f.write(str(port))

          self.socket = context.socket(zmq.PUSH)
          address = "tcp://127.0.0.1:%d" % port
          print("Binding pad %s to address %s" % (path, address))
          self.socket.bind(address)
        else:
          os.mkfifo(path)
          self.pipe = open(path, 'w', buffering=1)
        
        self.message = ""

    def __del__(self):
        """Closes the fifo."""
        if not self.tcp:
            self.pipe.close()
    
    def write(self, command, buffering=False):
        self.message += command + '\n'
        
        if not buffering:
            self.flush()
    
    def flush(self):
        if self.tcp:
            #print("sent message", self.message)
            self.socket.send_string(self.message)
        else:
            self.pipe.write(self.message)
        self.message = ""

    def press_button(self, button, buffering=False):
        """Press a button."""
        assert button in Button
        self.write('PRESS {}'.format(button.name), buffering)

    def release_button(self, button, buffering=False):
        """Release a button."""
        assert button in Button
        self.write('RELEASE {}'.format(button.name), buffering)

    def press_trigger(self, trigger, amount, buffering=False):
        """Press a trigger. Amount is in [0, 1], with 0 as released."""
        assert trigger in Trigger
        # assert 0 <= amount <= 1
        self.write('SET {} {:.2f}'.format(trigger.name, amount), buffering)

    def tilt_stick(self, stick, x, y, buffering=False):
        """Tilt a stick. x and y are in [0, 1], with 0.5 as neutral."""
        assert stick in Stick
        try:
          assert 0 <= x <= 1 and 0 <= y <= 1
        except AssertionError:
          import ipdb; ipdb.set_trace()
        self.write('SET {} {:.2f} {:.2f}'.format(stick.name, x, y), buffering)

    def send_controller(self, controller):
        for button in Button:
            field = 'button_' + button.name
            if hasattr(controller, field):
                if getattr(controller, field):
                    self.press_button(button, True)
                else:
                    self.release_button(button, True)

        # for trigger in Trigger:
        #     field = 'trigger_' + trigger.name
        #     self.press_trigger(trigger, getattr(controller, field))

        for stick in Stick:
            field = 'stick_' + stick.name
            value = getattr(controller, field)
            self.tilt_stick(stick, value.x, value.y, True)
        
        self.flush()
