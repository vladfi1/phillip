#!/usr/bin/env python3
import time
from dolphin import runDolphin
from argparse import ArgumentParser
from multiprocessing import Process
import random
import menu_manager

parser = ArgumentParser()

import RL
parser.add_argument("--model", choices=RL.models.keys(), required=True, help="which RL model to use")
parser.add_argument("--epsilon", type=float, default=0.02, help="probability of random action")
parser.add_argument("--temperature", type=float, default=0.01, help="increases action randomness")

#parser.add_argument("--policy", choices=["eps-greedy", "softmax"

parser.add_argument("--nozmq", dest="zmq", action="store_false", help="run with normal memory watcher (compatible with regular dolphin)")

parser.add_argument("--path", type=str,
                    help="where to import from and save to")

parser.add_argument("--name", type=str, help="sets path to saves/{name}")

parser.add_argument("--tag", type=int, help="optional tag to mark experiences")

parser.add_argument("--nodump", dest='dump', action="store_false", help="don't dump experiences to disk")

parser.add_argument("--parallel", type=int, help="spawn parallel cpus and dolphins")

parser.add_argument("--self_play", type=int, help="train against ourselves, reloading every N experiences")

parser.add_argument("--gpu", action="store_true", help="run on gpu")

parser.add_argument("--act_every", type=int, default=3, help="only take actions every ACT_EVERY frames")
parser.add_argument("--delay", type=int, default=0, help="delay actions by DELAY steps (multiplied by ACT_EVERY frames)")
parser.add_argument("--memory", type=int, default=0, help="how many frames to remember")
parser.add_argument("--experience_time", type=int, default=60, help="length of experiences, in seconds")

for i in [1, 2]:
  parser.add_argument("--p%d" % i, choices=menu_manager.characters.keys(), help="character for player %d" % i)

# some duplication going on here...
parser.add_argument("--dolphin", action="store_true", help="run dolphin")
parser.add_argument("--dolphin_dir", type=str, help="dolphin user directory")
parser.add_argument("--nosetup", dest="setup", action="store_false", help="don't setup dolphin directory")
parser.add_argument("--movie", type=str, help="movie to play on dolphin startup")
parser.add_argument("--gfx", type=str, default="Null", help="gfx backend")
parser.add_argument("--exe", type=str, default="dolphin-emu-headless", help="dolphin executable")
parser.add_argument("--gui", action="store_true", help="run dolphin with audio and graphics")
parser.add_argument("--mute", action="store_true", help="mute dolphin audio")
parser.add_argument("--dump_frames", action="store_true", help="dump frames from dolphin")
parser.add_argument("--iso", default="SSBM.iso", help="path to game iso")
parser.add_argument("--cpu_thread", action="store_true", help="emulate cpu on separate thread from gpu")

args = parser.parse_args()

if args.name is None:
  args.name = args.model

if args.path is None:
  args.path = "saves/%s/" % args.name

if args.parallel or args.gui:
  args.dolphin = True

prefix = args.dolphin_dir
if prefix is None:
  prefix = 'dolphin'

from cpu import CPU

def run():
  if args.dolphin_dir is None:
    tag = args.tag
    if tag is None:
      tag = random.getrandbits(32)
    user = '%s/%d/' % (prefix, tag)
    d = args.__dict__.copy()
    d['tag'] = tag
    d['dolphin_dir'] = user
  else:
    d = args.__dict__
    user = args.dolphin_dir
  
  cpu = CPU(**d)
  
  if args.dolphin:
    # delay for a bit to let the cpu start up
    time.sleep(3)
    dolphin = runDolphin(user=user, **args.__dict__)
  else:
    dolphin = None
  
  cpu.run(dolphin_process=dolphin)

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


