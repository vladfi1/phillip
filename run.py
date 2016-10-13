#!/usr/bin/env python3
import time
from dolphin import DolphinRunner
from argparse import ArgumentParser
from multiprocessing import Process
import random
import menu_manager
from movie import stages
from cpu import CPU
import RL

parser = ArgumentParser()

for opt in CPU.full_opts():
  opt.update_parser(parser)

for model in RL.models.values():
  for opt in model.full_opts():
    opt.update_parser(parser)

# dolphin options
parser.add_argument("--dolphin", action="store_true", help="run dolphin")

for opt in DolphinRunner.full_opts():
  opt.update_parser(parser)

args = parser.parse_args()

if args.gui:
  args.dolphin = True

if args.user is None:
  if args.tag is None:
    args.tag = random.getrandbits(32)
  args.user = 'dolphin/%d/' % args.tag

print("Creating cpu.")
cpu = CPU(**args.__dict__)

args.cpus = cpu.pids

if args.dolphin:
  dolphinRunner = DolphinRunner(**args.__dict__)
  # delay for a bit to let the cpu start up
  time.sleep(5)
  print("Running dolphin.")
  dolphin = dolphinRunner()
else:
  dolphin = None

print("Running cpu.")
cpu.run(dolphin_process=dolphin)

