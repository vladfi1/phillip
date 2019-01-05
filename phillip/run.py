#!/usr/bin/env python3
import time, os
import pprint
from phillip.dolphin import DolphinRunner
from argparse import ArgumentParser
from multiprocessing import Process
from phillip.cpu import CPU
from phillip import util
import tempfile

pp = pprint.PrettyPrinter(indent=2)

def run(**kwargs):
  load = kwargs.get('load')
  if load:
    params = util.load_params(load, 'agent')
  else:
    params = {}
  
  util.update(params, **kwargs)
  #pp.pprint(params)

  if params.get('gui'):
    params['dolphin'] = True

  if params.get('user') is None:
    params['user'] = tempfile.mkdtemp() + '/'
  
  if params.get('random_swap'):
    task_id = os.environ.get('SLURM_ARRAY_TASK_ID')
    if task_id is not None:
      params['swap'] = int(task_id) % 2
    else:
      import random
      params['swap'] = random.getrandbits(1)

  print("Creating cpu.")
  cpu = CPU(**params)

  params['cpus'] = cpu.pids

  if params.get('dolphin'):
    dolphinRunner = DolphinRunner(**params)
    # delay for a bit to let the cpu start up
    time.sleep(2)
    print("Running dolphin.")
    dolphin = dolphinRunner()
  else:
    dolphin = None

  print("Running cpu.")
  cpu.run(dolphin_process=dolphin)

def main():
  parser = ArgumentParser()

  for opt in CPU.full_opts():
    opt.update_parser(parser)

  parser.add_argument("--load", type=str, help="path to folder containing snapshot and params")

  # dolphin options
  parser.add_argument("--dolphin", action="store_true", default=None, help="run dolphin")
  
  parser.add_argument("--random_swap", action="store_true", help="randomly swap players")

  for opt in DolphinRunner.full_opts():
    opt.update_parser(parser)

  args = parser.parse_args()
  
  run(**args.__dict__)

if __name__ == "__main__":
  main()

