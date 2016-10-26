import os
import time
import RL
import util

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("--debug", action="store_true", help="set debug breakpoint")
parser.add_argument("-q", "--quiet", action="store_true", help="don't print status messages to stdout")
parser.add_argument("--init", action="store_true", help="initialize variables")

parser.add_argument("--sweeps", type=int, default=1, help="number of sweeps between saves")
parser.add_argument("--batches", type=int, default=1, help="number of batches per sweep")
parser.add_argument("--batch_size", type=int, default=1, help="number of trajectories per batch")
parser.add_argument("--batch_steps", type=int, default=1, help="number of gradient steps to take on each batch")

parser.add_argument("--dump", type=str, default="127.0.0.1", help="interface to listen on for experience dumps")

for opt in RL.Model.full_opts():
  opt.update_parser(parser)

for model in RL.models.values():
  for opt in model.full_opts():
    opt.update_parser(parser)

args = parser.parse_args()

model = RL.Model(mode=RL.Mode.TRAIN, **args.__dict__)

# do this in RL?
if args.init:
  model.init()
  model.save()
else:
  model.restore()

import zmq

context = zmq.Context()

socket = context.socket(zmq.PULL)
sock_addr = "tcp://%s:%d" % (args.dump, util.port(model.name))
print("Binding to " + sock_addr)
socket.bind(sock_addr)

import numpy as np
from collections import defaultdict
from gc import get_objects

def count_objects():
  counts = defaultdict(int)
  for obj in get_objects():
    counts[type(obj)] += 1
  return counts

def diff_objects(after, before):
  diff = {k: after[k] - before[k] for k in after}
  return {k: i for k, i in diff.items() if i}

sweep_size = args.batches * args.batch_size
sweeps = 0

before = count_objects()

while True:
  start_time = time.time()
  
  experiences = []
  
  for _ in range(sweep_size):
    experiences.append(socket.recv_pyobj())
  
  for _ in range(args.sweeps):
    from random import shuffle
    shuffle(experiences)
    
    for batch in util.chunk(experiences, args.batch_size):
      model.train(experiences, **args.__dict__)
  
  model.save()
  
  sweeps += 1
  total_time = time.time() - start_time
  
  if False:
    after = count_objects()
    print(diff_objects(after, before))
    before = after

  print(sweeps, total_time, sweep_size)

