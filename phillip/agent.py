import tensorflow as tf
from . import ssbm, RL, util, tf_lib as tfl, ctype_util as ct
import numpy as np
from numpy import random, exp
from .default import *
from .menu_manager import characters
import pprint
import os
import uuid
import pickle
from . import reward

pp = pprint.PrettyPrinter(indent=2)

class Agent(Default):
  _options = [
    Option('char', type=str, choices=characters.keys(), help="character that this agent plays as"),
    Option('verbose', action="store_true", default=False, help="print stuff while running"),
    Option('reload', type=int, default=60, help="reload model every RELOAD seconds"),
    Option('dump', type=int, help="dump experiences and receive parameters"),
    Option('trainer_id', type=str, help="trainer slurm job id"),
    Option('trainer_ip', type=str, help="trainer ip address"),
    Option('swap', type=int, default=0, help="swap players 1 and 2"),
    Option('disk', type=int, default=0, help="dump experiences to disk"),
    Option('real_delay', type=int, default=0, help="amount of delay in environment (due to netplay)"),
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
    self.probs = util.CircularQueue(self.rl.config.delay+1, 1.)
    self.history = util.CircularQueue(array=((self.rl.config.memory+1) * ssbm.SimpleStateAction)())
    
    self.hidden = util.deepMap(np.zeros, self.rl.core.hidden_size)
    self.prev_state = ssbm.GameMemory() # for rewards
    self.avg_reward = util.MovingAverage(.999)
    
    self.rl.restore()
    self.global_step = self.rl.get_global_step()

    self.dump = self.dump or self.trainer_id or self.trainer_ip
    
    if self.dump:
      try:
        import nnpy
      except ImportError as err:
        print("ImportError: {0}".format(err))
        sys.exit("Install nnpy to dump experiences")

      if not self.trainer_ip:
        ip_path = os.path.join(self.rl.path, 'ip')
        if os.path.exists(ip_path):
          with open(ip_path, 'r') as f:
            self.trainer_ip = f.read()
          print("Read ip from disk", self.trainer_ip)
        elif self.trainer_id:
          from . import om
          self.trainer_ip = om.get_job_ip(self.trainer_id)
          print("Got ip from trainer jobid", self.trainer_ip)
        else:
          import sys
          sys.exit("No trainer ip!")
      
      self.dump_socket = nnpy.Socket(nnpy.AF_SP, nnpy.PUSH)
      sock_addr = "tcp://%s:%d" % (self.trainer_ip, util.port(self.rl.path + "/experience"))
      print("Connecting experience socket to " + sock_addr)
      self.dump_socket.connect(sock_addr)

      self.params_socket = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
      self.params_socket.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, b"")
      self.params_socket.setsockopt(nnpy.SOL_SOCKET, nnpy.RCVMAXSIZE, -1)
      
      address = "tcp://%s:%d" % (self.trainer_ip, util.port(self.rl.path + "/params"))
      print("Connecting params socket to", address)
      self.params_socket.connect(address)

    # prepare experience buffer
    if self.dump or self.disk:
      self.dump_size = self.rl.config.experience_length
      self.dump_state_actions = (self.dump_size * ssbm.SimpleStateAction)()

      self.dump_frame = 0
      self.dump_count = 0
    
    if self.disk:
      self.dump_dir = os.path.join(self.rl.path, 'experience')
      print("Dumping to", self.dump_dir)
      util.makedirs(self.dump_dir)
      self.dump_tag = uuid.uuid4().hex

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
      prepared['global_step'] = self.global_step
      
      if self.dump:
        self.dump_socket.send(pickle.dumps(prepared))
      
      if self.disk:
        path = os.path.join(self.dump_dir, self.dump_tag + '_%d' % self.dump_count)
        with open(path, 'wb') as f:
          pickle.dump(prepared, f)


  def act(self, state, pad):
    self.frame_counter += 1
    if self.frame_counter % self.rl.config.act_every != 0:
      return
    
    verbose = self.verbose and (self.action_counter % (10 * self.rl.config.fps) == 0)
    #verbose = False
    
    r = reward.rewards_np(ct.vectorizeCTypes(ssbm.GameMemory, [self.prev_state, state]))[0]
    self.avg_reward.append(r)
    ct.copy(state, self.prev_state)
    
    if verbose:
      print("avg_reward: %f" % self.avg_reward.avg)
    
    current = self.history.peek()
    current.state = state # copy
    
    # extra copying, oh well
    if self.swap:
      current.state.players[0] = state.players[1]
      current.state.players[1] = state.players[0]
    
    current.prev_action = self.action

    self.history.increment()
    history = self.history.as_list()
    input_dict = ct.vectorizeCTypes(ssbm.SimpleStateAction, history)
    input_dict['hidden'] = self.hidden
    input_dict['delayed_action'] = self.actions.as_list()[1:]
    #print(input_dict['delayed_action'])
    
    (action, prob), self.hidden = self.rl.act(input_dict, verbose=verbose)

    #if verbose:
    #  pp.pprint(ct.toDict(state.players[1]))
    #  print(action)
    
    # the delayed action
    self.action = self.actions.push(action)
    current.action = self.action
    current.prob = self.probs.push(prob)
    
    # send a more recent action if the environment itself is delayed (netplay)
    real_action = self.actions[self.real_delay]
    self.rl.actionType.send(real_action, pad, self.char)
    
    self.action_counter += 1
    
    if self.dump or self.disk:
      self.dump_state(current)
    
    if self.reload:
      if self.dump:
        self.recieve_params()
      elif self.action_counter % (self.reload * self.rl.config.fps) == 0:
        self.rl.restore()
        self.global_step = self.rl.get_global_step()


  def recieve_params(self):
    if self.dump_frame != 0:
      return
    
    import nnpy
    num_blobs = 0
    latest = None
    
    # get the latest update from the trainer
    while True:
      try:
        #topic = self.socket.recv_string(zmq.NOBLOCK)
        blob = self.params_socket.recv(nnpy.DONTWAIT)
        params = pickle.loads(blob)
        self.global_step = params['global_step:0']
        latest = params
        """
        if global_step > self.global_step:
          self.global_step = global_step
          latest = params
        else:
          print("OUT OF ORDER?")
        """
        num_blobs += 1
      except nnpy.NNError as e:
        if e.error_no == nnpy.EAGAIN:
          # nothing to receive
          break
        # a real error
        raise e
    
    if latest is not None:
      print("Unblobbing", self.global_step)
      self.rl.unblob(latest)

    print("num_blobs", num_blobs)
