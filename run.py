#!/usr/bin/env python3
import time
from dolphin import runDolphin
from argparse import ArgumentParser
parser = ArgumentParser()


parser.add_argument("--model", choices=["DQN", "ActorCritic"], required=True, help="which RL model to use")

#parser.add_argument("--policy", choices=["eps-greedy", "softmax"

parser.add_argument("--path", type=str,
                    help="where to import from and save to")

parser.add_argument("--tag", type=str,
                    help="optional tag to mark experiences")

parser.add_argument("--nodump", dest='dump', action="store_false",
                    help="don't dump experiences to disk")

parser.add_argument("--dump_max", type=int,
                   help="caps number of experiences")

parser.add_argument("--dolphin_dir", type=str,
                   help="dolphin user directory")

parser.add_argument("--parallel", type=int, help="spawn parallel cpus")

# some duplication going on here...
#parser.add_argument("--dolphin", action="store_true", help="run dolphin")
parser.add_argument("--movie", type=str, help="movie to play on dolphin startup")
parser.add_argument("--gfx", type=str, help="gfx backend")
parser.add_argument("--exe", type=str, default="dolphin-emu-headless", help="dolphin executable")

args = parser.parse_args()

if args.path is None:
  args.path = "saves/%s/" % args.model

def runCPU(args):
  from cpu import CPU
  CPU(**args).run()

if args.parallel is None:
  runCPU(args.__dict__)
else:
  prefix = args.dolphin_dir
  if prefix is None:
    prefix = 'parallel'
  from multiprocessing import Process
  cpus = []
  dolphins = []
  
  for i in range(args.parallel):
    d = args.__dict__.copy()
    d['tag'] = i
    user = '%s/%d/' % (prefix, i)
    d['dolphin_dir'] = user
    runner = Process(target=runCPU, args=[d])
    runner.start()
    cpus.append(runner)

    dolphin = lambda: runDolphin(user=user, **args.__dict__)
    dolphins.append(dolphin)
  
  # give the runners some time to create the dolphin user directories
  time.sleep(2)
  
  # run the dolphins
  dolphins = [f() for f in dolphins]

  try:
    for c, d in zip(cpus, dolphins):
      c.join()
      d.wait()
  except KeyboardInterrupt:
    for c, d in zip(cpus, dolphins):
      c.terminate()
      d.terminate()

