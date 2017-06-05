import os, sys
import time
from phillip import RL, util
from phillip.default import *
import numpy as np
from collections import defaultdict
import zmq
import resource
import gc
import tensorflow as tf
#from memory_profiler import profile
import netifaces

# some helpers for debugging memory leaks

def count_objects():
  counts = defaultdict(int)
  for obj in gc.get_objects():
    counts[type(obj)] += 1
  return counts

def diff_objects(after, before):
  diff = {k: after[k] - before[k] for k in after}
  return {k: i for k, i in diff.items() if i}

class Trainer(Default):
  _options = [
    #Option("debug", action="store_true", help="set debug breakpoint"),
    #Option("-q", "--quiet", action="store_true", help="don't print status messages to stdout"),
    Option("init", action="store_true", help="initialize variables"),

    Option("sweeps", type=int, default=1, help="number of sweeps between saves"),
    Option("sweep_limit", type=int, default=-1),
    Option("batches", type=int, default=1, help="number of batches per sweep"),
    Option("batch_size", type=int, default=1, help="number of trajectories per batch"),
    Option("batch_steps", type=int, default=1, help="number of gradient steps to take on each batch"),
    Option("min_collect", type=int, default=1, help="minimum number of experiences to collect between sweeps"),
    Option("max_age", type=int, default=10, help="how old an experience can be before we discard it"),
    
    Option("log_interval", type=int, default=10),
    Option("dump", type=str, default="lo", help="interface to listen on for experience dumps"),
    Option('send', type=int, default=1, help="send the network parameters on a zmq PUB socket"),
    Option("save_interval", type=float, default=10, help="length of time between saves to disk, in minutes"),

    Option("load", type=str, help="path to a json file from which to load params"),

    Option('objgraph', type=int, default=0, help='use objgraph to track memory usage'),
  ]
  
  _members = [
    ("model", RL.RL),
  ]
  
  def __init__(self, load=None, **kwargs):
    if load is None:
      args = {}
    else:
      args = util.load_params(load, 'train')
    
    util.update(args, mode=RL.Mode.TRAIN, **kwargs)
    util.pp.pprint(args)
    Default.__init__(self, **args)

    addresses = netifaces.ifaddresses(self.dump)
    address = addresses[netifaces.AF_INET][0]['addr']

    with open(os.path.join(self.model.path, 'ip'), 'w') as f:
      f.write(address)

    context = zmq.Context.instance()

    self.experience_socket = context.socket(zmq.PULL)
    experience_addr = "tcp://%s:%d" % (address, util.port(self.model.name + "/experience"))
    self.experience_socket.bind(experience_addr)

    if self.send:
      import nnpy
      self.params_socket = nnpy.Socket(nnpy.AF_SP, nnpy.PUB)
      params_addr = "tcp://%s:%d" % (address, util.port(self.model.name + "/params"))
      print("Binding params socket to", params_addr)
      self.params_socket.bind(params_addr)

    self.sweep_size = self.batches * self.batch_size
    print("Sweep size", self.sweep_size)
    
    if self.init:
      self.model.init()
      self.model.save()
    else:
      self.model.restore()
    
    self.last_save = time.time()
  
  def save(self):
    current_time = time.time()
    
    if current_time - self.last_save > 60 * self.save_interval:
      try:
        self.model.save()
        self.last_save = current_time
      except tf.errors.InternalError as e:
        print(e, file=sys.stderr)

  def train(self):
    before = count_objects()

    sweeps = 0
    step = 0

    experiences = []
    
    while sweeps != self.sweep_limit:
      start_time = time.time()
      
      print('Start: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      age_limit = self.model.get_global_step() - self.max_age
      is_valid = lambda exp: exp['global_step'] >= age_limit
      experiences = list(filter(is_valid, experiences))
      
      collected = 0
      while len(experiences) < self.sweep_size:
        exp = self.experience_socket.recv_pyobj()
        if is_valid(exp):
          experiences.append(exp)
          collected += 1

      # pull in all the extra experiences
      for _ in range(self.sweep_size):
        try:
          exp = self.experience_socket.recv_pyobj(zmq.NOBLOCK)
          if is_valid(exp):
            experiences.append(exp)
            collected += 1
        except zmq.ZMQError:
          break
      
      print('After collect: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      collect_time = time.time()
      
      for _ in range(self.sweeps):
        from random import shuffle
        shuffle(experiences)

        batch_size = len(experiences) // self.batches
        for batch in util.chunk(experiences, batch_size):
          self.model.train(batch, self.batch_steps, log=(step%self.log_interval==0))
          step += 1
      
      print('After train: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      train_time = time.time()

      if self.send:
        #self.params_socket.send_string("", zmq.SNDMORE)
        params = self.model.blob()
        blob = pickle.dumps(params)
        print('After blob: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.params_socket.send(blob)
        print('After send: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      self.save()
      
      #print('After save: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      save_time = time.time()
      
      sweeps += 1
      
      if False:
        after = count_objects()
        print(diff_objects(after, before))
        before = after
      
      save_time -= train_time
      train_time -= collect_time
      collect_time -= start_time
      
      print(sweeps, len(experiences), collected, collect_time, train_time, save_time)
      print('Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      if self.objgraph:
        import objgraph
        #gc.collect()  # don't care about stuff that would be garbage collected properly
        objgraph.show_growth()

if __name__ == '__main__':
  from argparse import ArgumentParser
  parser = ArgumentParser()

  for opt in Trainer.full_opts():
    opt.update_parser(parser)

  for policy in RL.policies.values():
    for opt in policy.full_opts():
      opt.update_parser(parser)

  args = parser.parse_args()
  trainer = Trainer(**args.__dict__)
  trainer.train()

