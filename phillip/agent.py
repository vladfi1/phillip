import tensorflow as tf
from . import ssbm, actor, util, tf_lib as tfl, ctype_util as ct
import numpy as np
from numpy import random, exp
from .default import *
from .menu_manager import characters
import pprint
import os
import time
import uuid
import pickle
from . import reward

pp = pprint.PrettyPrinter(indent=2)

class Agent(Default):
  _options = [
    Option('char', type=str, choices=characters.keys(), help="character that this agent plays as"),
    Option('verbose', action="store_true", default=False, help="print stuff while running"),
    Option('reload', type=int, default=60, help="reload model every RELOAD seconds"),
    Option('dump', type=int, help="dump experiences over network"),
    Option('receive', action="store_true", help="receive parameters over network"),
    Option('trainer_id', type=str, help="trainer slurm job id"),
    Option('trainer_ip', type=str, help="trainer ip address"),
    Option('swap', type=int, default=0, help="swap players 1 and 2"),
    Option('disk', type=int, default=0, help="dump experiences to disk"),
    Option('real_delay', type=int, default=0, help="amount of delay in environment (due to netplay)"),
    Option('tb', action="store_true", help="log stats to tensorboard"),
  ]
  
  _members = [
    ('actor', actor.Actor)
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)

    self.pid = 0 if self.swap else 1
    self.frame_counter = 0
    self.action_chain = None
    self.action_counter = np.random.randint(0, self.reload+1)  # to desynch actors
    self.action = 0
    self.actions = util.CircularQueue(self.actor.config.delay+1, 0)
    self.probs = util.CircularQueue(self.actor.config.delay+1, 1.)
    self.history = util.CircularQueue(array=((self.actor.config.memory+1) * ssbm.SimpleStateAction)())
    
    self.hidden = util.deepMap(np.zeros, self.actor.core.hidden_size)
    self.prev_state = ssbm.GameMemory() # for rewards
    avg_minutes = 30
    self.avg_reward = util.MovingAverage(1./(self.actor.config.fps * 60 * avg_minutes))
    
    self.actor.restore()
    self.global_step = self.actor.get_global_step()

    self.dump = self.dump or self.trainer_id or self.trainer_ip
    self.receive = self.dump or self.receive
    
    if self.receive:
      self.update_ip()
      self.make_sockets()

    # prepare experience buffer
    if self.dump or self.disk:
      self.dump_size = self.actor.config.experience_length
      self.dump_state_actions = (self.dump_size * ssbm.SimpleStateAction)()

      self.dump_frame = 0
      self.dump_count = 0
    
    if self.disk:
      self.dump_dir = os.path.join(self.actor.path, 'experience')
      print("Dumping to", self.dump_dir)
      util.makedirs(self.dump_dir)
      self.dump_tag = uuid.uuid4().hex
    
    if self.tb:
      self.writer = tf.summary.FileWriterCache.get(self.actor.path)

  def update_ip(self):
    ip_path = os.path.join(self.actor.path, 'ip')
    if os.path.exists(ip_path):
      with open(ip_path, 'r') as f:
        trainer_ip = f.read()
      print("Read ip from disk", self.trainer_ip)
    elif self.trainer_id:
      from . import om
      trainer_ip = om.get_job_ip(self.trainer_id)
      print("Got ip from trainer jobid", self.trainer_ip)
    elif not self.trainer_ip:
      import sys
      sys.exit("No trainer ip!")
    else:
      trainer_ip = self.trainer_ip

    self.ip_check_time = time.time()
    if trainer_ip != self.trainer_ip:
      self.trainer_ip = trainer_ip
      return True
    return False

  def make_sockets(self):
    """Updates trainer_ip from disk. Returns True if it has changed."""
    try:
      import nnpy
    except ImportError as err:
      print("ImportError: {0}".format(err))
      sys.exit("Install nnpy to dump experiences")

    if self.dump:
      self.dump_socket = nnpy.Socket(nnpy.AF_SP, nnpy.PUSH)
      sock_addr = "tcp://%s:%d" % (self.trainer_ip, util.port(self.actor.path + "/experience"))
      print("Connecting experience socket to " + sock_addr)
      self.dump_socket.connect(sock_addr)

    self.params_socket = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
    self.params_socket.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, b"")
    self.params_socket.setsockopt(nnpy.SOL_SOCKET, nnpy.RCVMAXSIZE, -1)
    
    address = "tcp://%s:%d" % (self.trainer_ip, util.port(self.actor.path + "/params"))
    print("Connecting params socket to", address)
    self.params_socket.connect(address)

  def dump_state(self, state_action):
    #print(self.frame_counter)
    # TODO: figure out what's wrong with early frames
    if self.frame_counter < 300:
      return
    
    self.dump_state_actions[self.dump_frame] = state_action
    
    if self.dump_frame == 0:
      self.initial = self.hidden

    self.dump_frame += 1

    if self.dump_frame == self.dump_size:
      self.dump_count += 1
      self.dump_frame = 0
      
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

  # Given the current state, determine the action you'll take and send it to the Smash emulator. 
  # pad is a "game pad" object, for interfacing with the emulator
  def act(self, state, pad):
    verbose = self.verbose and (self.frame_counter % 600 == 0)
    self.frame_counter += 1
    #verbose = False
    
    if self.action_chain is not None and not self.action_chain.done():
      self.action_chain.act(pad, state.players[self.pid], self.char)
      return
    
    r = reward.computeRewards([self.prev_state, state], damage_ratio=0)[0]
    self.avg_reward.append(r)
    ct.copy(state, self.prev_state)

    score_per_minute = self.avg_reward.avg * self.actor.config.fps * 60
    if self.tb and self.frame_counter % 3600:  # once per minute
      summary = tf.summary.Summary()
      summary.value.add(tag='score_per_minute', simple_value=score_per_minute)
      self.writer.add_summary(summary, self.actor.get_global_step())

    if verbose:
      print("score_per_minute: %f" % score_per_minute)
    
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
    
    (action, prob), self.hidden = self.actor.act(input_dict, verbose=verbose)

    #if verbose:
    #  pp.pprint(ct.toDict(state.players[1]))
    #  print(action)
    
    # the delayed action
    self.action = self.actions.push(action)
    current.action = self.action
    current.prob = self.probs.push(prob)
    
    # send a more recent action if the environment itself is delayed (netplay)
    real_action = self.actions[self.real_delay]
    self.action_chain = self.actor.actionType.choose(real_action, self.actor.config.act_every)
    self.action_chain.act(pad, state.players[self.pid], self.char)
    
    self.action_counter += 1
    
    if self.dump or self.disk:
      self.dump_state(current)
    
    if self.reload:
      if self.receive:
        self.receive_params()
      elif self.action_counter % (self.reload * self.actor.config.fps) == 0:
        self.actor.restore()
        self.global_step = self.actor.get_global_step()

    # check if trainer ip has changed each hour
    if self.receive and time.time() - self.ip_check_time > 60 * 60:
      if self.update_ip():
        self.make_sockets()

  # When called, ask the learner if there are new parameters. 
  def receive_params(self):
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
      self.actor.unblob(latest)
