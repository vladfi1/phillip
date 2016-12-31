import tensorflow as tf
import ssbm
import tf_lib as tfl
import numpy as np
from numpy import random, exp
import RL
import util
from default import *
from menu_manager import characters
import ctype_util as ct
import pprint

pp = pprint.PrettyPrinter(indent=2)

class Agent(Default):
  _options = [
    Option('delay', type=int, default=0, help="delay actions this many rounds"),
    Option('char', type=str, choices=characters.keys(), help="character that this agent plays as"),
    Option('verbose', action="store_true", default=False, help="print stuff while running"),
    Option('reload', type=int, default=60, help="reload model every RELOAD seconds"),
    Option('listen', type=str, help="address to listen on for model updates"), #TODO: merge with cpu dump
  ]
  
  _members = [
    ('model', RL.Model)
  ]
  
  def __init__(self, **kwargs):
    kwargs = kwargs.copy()
    kwargs.update(mode=RL.Mode.PLAY)
    Default.__init__(self, **kwargs)
    
    self.counter = 0
    self.action = 0
    self.actions = util.CircularQueue(self.delay+1, 0)
    self.memory = util.CircularQueue(array=((self.model.memory+1) * ssbm.SimpleStateAction)())
    
    self.hidden = util.deepMap(np.zeros, self.model.model.hidden_size)
    
    self.model.restore()
    
    if self.listen:
      import zmq
      context = zmq.Context.instance()
      self.socket = context.socket(zmq.SUB)
      self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
      address = "tcp://%s:%d" % (self.listen, util.port(self.model.name + "/params"))
      print("Connecting params socket to", address)
      self.socket.connect(address)

  def act(self, state, pad):
    verbose = self.verbose and (self.counter % (10 * self.model.rlConfig.fps) == 0)
    #verbose = False
    
    current = self.memory.peek()
    current.state = state
    
    self.prev_action = self.action
    current.prev_action = self.prev_action

    self.memory.increment()
    history = self.memory.as_list()
    
    history = ct.vectorizeCTypes(ssbm.SimpleStateAction, history)
    history['hidden'] = self.hidden
    
    self.action, self.hidden = self.model.act(history, verbose)
    
    current.action = self.action

    #if verbose:
    #  pp.pprint(ct.toDict(state.players[1]))
    #  print(self.action)
    
    # the delayed action
    action = self.actions.push(self.action)

    # TODO: make the banned action system more robust
    
    # prevent peach from using toad
    # for some reason it causes both agents to use action 0
    if self.char == 'peach' and action == 22:
      action = 4
    
    # prevent sheik and zelda from transforming
    if self.char in ['zelda', 'sheik'] and action in [18, 21, 24]:
      action = 4

    controller = ssbm.simpleControllerStates[action]
    pad.send_controller(controller.realController())

    self.counter += 1

    if self.reload and self.counter % (self.reload * self.model.rlConfig.fps) == 0:
      if self.listen:
        import zmq
        blob = None
        
        # get the latest update from the trainer
        while True:
          try:
            topic = self.socket.recv_string(zmq.NOBLOCK)
            blob = self.socket.recv_pyobj(zmq.NOBLOCK)
          except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
              # nothing to receive
              break
            # a real error
            raise e
        
        if blob is not None:
          print("unblobbing")
          self.model.unblob(blob)
        else:
          print("no blob received")
      else:
        self.model.restore()

