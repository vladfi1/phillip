import tensorflow as tf
from phillip import ssbm, util, RL
from phillip.default import *
import pickle
from random import shuffle
import time
import os

experience_length = 6000

def load_experience(path):
  with open(path, 'rb') as f:
    return pickle.load(f)

class ModelTrainer(Default):
  _options = [
    Option('data', type=str, help='path to experience folder'),
    Option('load', type=str, help='path to params + snapshot'),
    Option('init', action='store_true'),
    Option('batch_size', type=int, default=1),
    Option('valid_batches', type=int, default=1),
    Option('epochs', type=int, default=1000000),
  ]
  
  _members = [
    ('rl', RL.RL),
  ]

  def __init__(self, load=None, **kwargs):
    if load is None:
      args = {}
    else:
      args = util.load_params(load, 'train')
    
    kwargs.update(
        train_model=1,
        train_actor=0,
        train_critic=0,
        experience_length=6000,
    )
    util.update(args,
        mode=RL.Mode.TRAIN,
        **kwargs
    )
    util.pp.pprint(args)
    Default.__init__(self, **args)

    if self.init:
      self.rl.init()
      self.rl.save()
    else:
      self.rl.restore()
    
    if self.data is None:
      self.data = os.path.join(self.rl.path, 'experience')
    
    print("Loading experiences from", self.data)
     
    files = os.listdir(self.data)
    data_paths = [os.path.join(self.data, f) for f in files]
    
    print("Loading %d experiences." % len(files))
    

    self.experiences = []
    parallel = True
    
    if parallel:
      for paths in util.chunk(data_paths, 100):
        self.experiences = util.async_map(load_experience, paths)()
    else:
      for path in data_paths:
        with open(path, 'rb') as f:
          self.experiences.append(pickle.load(f))

    self.valid_size = self.valid_batches * self.batch_size  

  def train(self):
    valid_set = self.experiences[:self.valid_size]
    train_set = self.experiences[self.valid_size:]
    
    valid_batches = util.chunk(valid_set, self.batch_size)
    
    for epoch in range(self.epochs):
      print("Epoch", epoch)
      start_time = time.time()
      
      shuffle(train_set)
      batches = util.chunk(train_set, self.batch_size)
      
      for batch in batches:
        self.rl.train(batch)
      
      print(time.time() - start_time) 
      
      self.rl.save()

def main(**kwargs):
  ModelTrainer(**kwargs).train()

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser()

  for opt in ModelTrainer.full_opts():
    opt.update_parser(parser)

  args = parser.parse_args()
  main(**args.__dict__)

