import os
import sys
import time
from phillip import RL, util
from phillip.default import *
import numpy as np
from collections import defaultdict
import zmq
import resource
import gc
import objgraph
import tensorflow as tf

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
    Option("batches", type=int, default=1, help="number of batches per sweep"),
    Option("batch_size", type=int, default=1, help="number of trajectories per batch"),
    Option("batch_steps", type=int, default=1, help="number of gradient steps to take on each batch"),
    Option("min_collect", type=int, default=1, help="minimum number of experiences to collect between sweeps"),

    Option("dump", type=str, default="lo", help="interface to listen on for experience dumps"),
    
    Option("save_interval", type=float, default=10, help="length of time between saves to disk, in minutes"),

    Option("load", type=str, help="path to a json file from which to load params"),
  ]
  
  _members = [
    ("model", RL.Model),
  ]
  
  def __init__(self, load=None, **kwargs):
    if load is None:
      args = {}
    else:
      args = util.load_params(load, 'train')
      
    util.update(args, mode=RL.Mode.TRAIN, **kwargs)
    print(args)
    Default.__init__(self, **args)
    
    if self.init:
      self.model.init()
      self.model.save()
    else:
      self.model.restore()

    context = zmq.Context.instance()

    self.experience_socket = context.socket(zmq.PULL)
    experience_addr = "tcp://%s:%d" % (self.dump, util.port(self.model.name + "/experience"))
    self.experience_socket.bind(experience_addr)
    
    self.params_socket = context.socket(zmq.PUB)
    params_addr = "tcp://%s:%d" % (self.dump, util.port(self.model.name + "/params"))
    print("Binding params socket to", params_addr)
    self.params_socket.bind(params_addr)

    self.sweep_size = self.batches * self.batch_size
    print("Sweep size", self.sweep_size)
    
    self.buffer = util.CircularQueue(self.sweep_size)
    
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
    
    for _ in range(self.sweep_size):
      self.buffer.push(self.experience_socket.recv_pyobj())
    
    print("Buffer filled")
    
    while True:
      start_time = time.time()
      
      #print('Start: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      for _ in range(self.min_collect):
        self.buffer.push(self.experience_socket.recv_pyobj())

      collected = self.min_collect
      
      while True:
        try:
          self.buffer.push(self.experience_socket.recv_pyobj(zmq.NOBLOCK))
          collected += 1
        except zmq.ZMQError as e:
          break
      
      #print('After collect: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      collect_time = time.time()
      
      experiences = self.buffer.as_list()
      
      for _ in range(self.sweeps):
        from random import shuffle
        shuffle(experiences)
        
        for batch in util.chunk(experiences, self.batch_size):
          self.model.train(batch, self.batch_steps)
      
      print('After train: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      train_time = time.time()
      
      #self.params_socket.send_string("", zmq.SNDMORE)
      self.params_socket.send_pyobj(self.model.blob())
      
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
      
      print(sweeps, self.sweep_size, collected, collect_time, train_time, save_time)
      print('Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      
      #gc.collect()  # don't care about stuff that would be garbage collected properly
      #objgraph.show_growth()

if __name__ == '__main__':
  from argparse import ArgumentParser
  parser = ArgumentParser()

  for opt in Trainer.full_opts():
    opt.update_parser(parser)

  for model in RL.models.values():
    for opt in model.full_opts():
      opt.update_parser(parser)

  args = parser.parse_args()
  trainer = Trainer(**args.__dict__)
  trainer.train()

