#!/usr/bin/env python3
import time
from dolphin import runDolphin
from argparse import ArgumentParser
from multiprocessing import Process
import random
import os

# don't use gpu
# TODO: set this in tensorflow
os.environ["CUDA_VISIBLE_DEVICES"] = ""

parser = ArgumentParser()

parser.add_argument("--model", choices=["DQN", "ActorCritic"], required=True, help="which RL model to use")

#parser.add_argument("--policy", choices=["eps-greedy", "softmax"

parser.add_argument("--path", type=str,
                    help="where to import from and save to")

parser.add_argument("--name", type=str, help="sets path to saves/{name}")

parser.add_argument("--tag", type=str,
                    help="optional tag to mark experiences")

parser.add_argument("--nodump", dest='dump', action="store_false",
                    help="don't dump experiences to disk")

parser.add_argument("--dump_max", type=int,
                   help="caps number of experiences")

parser.add_argument("--dolphin_dir", type=str,
                   help="dolphin user directory")

parser.add_argument("--dolphin", action="store_true", help="run dolphin")
parser.add_argument("--nosetup", dest="setup", action="store_false", help="don't setup dolphin directory")
parser.add_argument("--parallel", type=int, help="spawn parallel cpus and dolphins")

parser.add_argument("--self_play", action="store_true", help="train against ourselves")

# some duplication going on here...
parser.add_argument("--movie", type=str, help="movie to play on dolphin startup")
parser.add_argument("--gfx", type=str, help="gfx backend")
parser.add_argument("--exe", type=str, default="dolphin-emu-headless", help="dolphin executable")
parser.add_argument("--dump_frames", action="store_true", help="dump frames from dolphin")

args = parser.parse_args()

if args.name is None:
  args.name = args.model

if args.path is None:
  args.path = "saves/%s/" % args.name

if args.parallel:
  args.dolphin = True

prefix = args.dolphin_dir
if prefix is None:
  prefix = 'dolphin'

from cpu import runCPU

def run():
  if args.dolphin_dir is None:
    tag = random.getrandbits(32)
    user = '%s/%d/' % (prefix, tag)
    d = args.__dict__.copy()
    d['tag'] = tag
    d['dolphin_dir'] = user
  else:
    d = args.__dict__
    user = args.dolphin_dir
  
  cpu = Process(target=runCPU, kwargs=d)
  cpu.start()
  
  if args.dolphin:
    # delay for a bit to let the cpu start up
    time.sleep(5)
    dolphin = runDolphin(user=user, **args.__dict__)
    
    try:
      dolphin.wait()
      cpu.terminate()
    except KeyboardInterrupt:
      dolphin.terminate()
      cpu.terminate()
  else:
    cpu.join()

if args.parallel is None:
  run()
else:
  runners = []
  
  for _ in range(args.parallel):
    runner = Process(target=run)
    runner.start()
    runners.append(runner)
  
  try:
    for runner in runners:
      runner.join()
  except KeyboardInterrupt:
    for runner in runners:
      runner.terminate()


