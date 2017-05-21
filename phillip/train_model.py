from phillip import ssbm, util, RL
from phillip.default import Default, Option
import hickle
import time

class ModelTrainer(Default):
  _options = [
    Option('data', type=str, help='path to experience file'),
    Option('load', type=str, help='path to params + snapshot'),
    Option('init', action='store_true'),
    Option('batch_size', type=int, default=1),
    Option('valid_batches', type=int, default=1),
    Option('file_limit', type=int, default=0, help="0 means no limit"),
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
    
    print("Loading experiences from", self.data)
    
    start_time = time.time()
    self.experiences = hickle.load(self.data)
    print("Loaded experiences in %d seconds." % (time.time() - start_time))
    if 'initial' not in self.experiences:
      self.experiences['initial'] = []

  def train(self):
    shape = self.experiences['action'].shape
    data_size = shape[0]
    
    batches = []
    for i in range(0, data_size, self.batch_size):
      batches.append(util.deepMap(lambda t: t[i:i+self.batch_size], self.experiences))
  
    valid_batches = batches[:self.valid_batches]
    train_batches = batches[self.valid_batches:]
    
    for epoch in range(self.epochs):
      print("Epoch", epoch)
      start_time = time.time()
      
      for batch in train_batches:
        self.rl.train(batch, log=False, zipped=True)
      
      print(time.time() - start_time) 
      
      for batch in valid_batches:
        self.rl.train(batch, train=False, zipped=True)

      self.rl.save()

      import resource
      print('Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def main(**kwargs):
  ModelTrainer(**kwargs).train()

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser()

  for opt in ModelTrainer.full_opts():
    opt.update_parser(parser)

  args = parser.parse_args()
  main(**args.__dict__)

