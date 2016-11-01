#!/usr/bin/env python3
import time
from dolphin import DolphinRunner
from argparse import ArgumentParser
from multiprocessing import Process
import random
from cpu import CPU
import RL
import util

parser = ArgumentParser()

for opt in CPU.full_opts():
  opt.update_parser(parser)

for model in RL.models.values():
  for opt in model.full_opts():
    opt.update_parser(parser)

# dolphin options
parser.add_argument("--dolphin", action="store_true", default=None, help="run dolphin")
parser.add_argument("--params", type=str, help="path to a json file from which to load params")

for opt in DolphinRunner.full_opts():
  opt.update_parser(parser)

args = parser.parse_args()

if args.params:
  import json
  with open(args.params) as f:
    params = json.load(f)['agent']
else:
  params = {}

util.update(params, **args.__dict__)
print(params)

if params['gui']:
  params['dolphin'] = True

if params['user'] is None:
  if params['tag'] is None:
    params['tag'] = random.getrandbits(32)
  params['user'] = 'dolphin/%d/' % params['tag']

print("Creating cpu.")
cpu = CPU(**params)

params['cpus'] = cpu.pids

if params['dolphin']:
  dolphinRunner = DolphinRunner(**params)
  # delay for a bit to let the cpu start up
  time.sleep(5)
  print("Running dolphin.")
  dolphin = dolphinRunner()
else:
  dolphin = None

print("Running cpu.")
cpu.run(dolphin_process=dolphin)

