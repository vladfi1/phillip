#!/usr/bin/env python3
import time
from dolphin import DolphinRunner
from argparse import ArgumentParser
from multiprocessing import Process
from cpu import CPU
import RL
import util
import tempfile

parser = ArgumentParser()

for opt in CPU.full_opts():
  opt.update_parser(parser)

for model in RL.models.values():
  for opt in model.full_opts():
    opt.update_parser(parser)

parser.add_argument("--load", type=str, help="path to folder containing snapshot and params")

# dolphin options
parser.add_argument("--dolphin", action="store_true", default=None, help="run dolphin")

for opt in DolphinRunner.full_opts():
  opt.update_parser(parser)

args = parser.parse_args()

if args.load:
  params = util.load_params(args.load, 'agent')
else:
  params = {}

util.update(params, **args.__dict__)
print(params)

if params['gui']:
  params['dolphin'] = True

if params['user'] is None:
  params['user'] = tempfile.mkdtemp() + '/'

print("Creating cpu.")
cpu = CPU(**params)

params['cpus'] = cpu.pids

if params['dolphin']:
  dolphinRunner = DolphinRunner(**params)
  # delay for a bit to let the cpu start up
  time.sleep(2)
  print("Running dolphin.")
  dolphin = dolphinRunner()
else:
  dolphin = None

print("Running cpu.")
cpu.run(dolphin_process=dolphin)

