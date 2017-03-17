import tensorflow as tf
from . import ssbm, RL, util, tf_lib as tfl, ctype_util as ct
import numpy as np
from numpy import random, exp
from .default import *
from .menu_manager import characters
import pprint

pp = pprint.PrettyPrinter(indent=2)

class Agent(Default):
  _options = [
    Option('char', type=str, choices=characters.keys(), help="character that this agent plays as"),
    Option('verbose', action="store_true", default=False, help="print stuff while running"),
    Option('reload', type=int, default=60, help="reload model every RELOAD seconds"),
    Option('dump', type=str, help="dump experiences to ip address via zmq"),
    Option('listen', type=str, help="address to listen on for model updates"),
    Option('swap', type=int, default=0, help="swap players 1 and 2"),
  ]
  
  _members = [
    ('rl', RL.RL)
  ]
  
  def __init__(self, **kwargs):
    kwargs = kwargs.copy()
    kwargs.update(mode=RL.Mode.PLAY)
    Default.__init__(self, **kwargs)
    
    self.frame_counter = 0
    self.action_counter = 0
    self.action = 0
    self.actions = util.CircularQueue(self.rl.config.delay+1, 0)
    self.history = util.CircularQueue(array=((self.rl.config.memory+1) * ssbm.SimpleStateAction)())
    
    self.hidden = util.deepMap(np.zeros, self.rl.policy.hidden_size)
    
    self.rl.restore()
    
    # TODO: merge dump and listen, they should always use the same address?
    if self.dump:
      try:
        import zmq
      except ImportError as err:
        print("ImportError: {0}".format(err))
        sys.exit("Install pyzmq to dump experiences")
      
      context = zmq.Context.instance()

      self.dump_socket = context.socket(zmq.PUSH)
      sock_addr = "tcp://%s:%d" % (self.dump, util.port(self.rl.name + "/experience"))
      print("Connecting experience socket to " + sock_addr)
      self.dump_socket.connect(sock_addr)
      
      self.dump_size = self.rl.config.experience_length
      self.dump_state_actions = (self.dump_size * ssbm.SimpleStateAction)()

      self.dump_frame = 0
      self.dump_count = 0

    if self.listen:
      import zmq
      context = zmq.Context.instance()
      self.params_socket = context.socket(zmq.SUB)
      self.params_socket.setsockopt(zmq.SUBSCRIBE, b"")
      address = "tcp://%s:%d" % (self.listen, util.port(self.rl.name + "/params"))
      print("Connecting params socket to", address)
      self.params_socket.connect(address)

  def dump_state(self, state_action):
    self.dump_state_actions[self.dump_frame] = state_action
    
    if self.dump_frame == 0:
      self.initial = self.hidden

    self.dump_frame += 1

    if self.dump_frame == self.dump_size:
      self.dump_count += 1
      self.dump_frame = 0
      
      if self.dump_count == 1:
        return # FIXME: figure out what is wrong with the first experience
      
      print("Dumping", self.dump_count)
      
      prepared = ssbm.prepareStateActions(self.dump_state_actions)
      prepared['initial'] = self.initial
      
      self.dump_socket.send_pyobj(prepared)

  def act(self, state, pad):
    self.frame_counter += 1
    if self.frame_counter % self.rl.config.act_every != 0:
      return
    
    verbose = self.verbose and (self.action_counter % (10 * self.rl.config.fps) == 0)
    #verbose = False
    
    current = self.history.peek()
    current.state = state # copy
    
    # extra copying, oh well
    if self.swap:
      current.state.players[0] = state.players[1]
      current.state.players[1] = state.players[0]
    
    current.prev_action = self.action

    self.history.increment()
    history = self.history.as_list()
    
    history = ct.vectorizeCTypes(ssbm.SimpleStateAction, history)
    history['hidden'] = self.hidden
    
    self.action, p, self.hidden = self.rl.act(history, verbose)
    
    current.prob = p
    current.action = self.action

    #if verbose:
    #  pp.pprint(ct.toDict(state.players[1]))
    #  print(self.action)
    
    # the delayed action
    action = self.actions.push(self.action)
    
    self.rl.actionType.send(action, pad, self.char)
    
    self.action_counter += 1
    
    if self.dump:
      self.dump_state(current)
    
    if self.reload and self.action_counter % (self.reload * self.rl.config.fps) == 0:
      if self.listen:
        import zmq
        blob = None
        
        # get the latest update from the trainer
        while True:
          try:
            #topic = self.socket.recv_string(zmq.NOBLOCK)
            blob = self.params_socket.recv_pyobj(zmq.NOBLOCK)
          except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
              # nothing to receive
              break
            # a real error
            raise e
        
        if blob is not None:
          print("unblobbing")
          self.rl.unblob(blob)
        else:
          print("no blob received")
      else:
        self.rl.restore()

