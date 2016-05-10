#!/usr/bin/env python3
from argparse import ArgumentParser
parser = ArgumentParser()

parser.add_argument("--name", type=str,
                    help="filename to import from and save to")

parser.add_argument("--tag", type=str,
                    help="optional tag to mark experiences")

parser.add_argument("--nodump", dest='dump', action="store_false",
                    help="don't dump experiences to disk")

parser.add_argument("--dump_max", type=int,
                   help="caps number of experiences")

parser.add_argument("--dump_seconds", type=int,
                   help="how many seconds of experience in each file")

parser.add_argument("--dolphin_dir", type=str,
                   help="dolphin user directory")

parser.add_argument("--parallel", type=int, help="spawn parallel cpus")

args = parser.parse_args()

def runCPU(args):
  from cpu import CPU
  CPU(**args).run()

if args.parallel is None:
  runCPU(args.__dict__)
else:
  from multiprocessing import Process
  processes = []
  for i in range(args.parallel):
    d = args.__dict__.copy()
    d['tag'] = i
    d['dolphin_dir'] = 'parallel/%d/' % i
    p = Process(target=runCPU, args=[d])
    p.start()
    processes.append(p)

  try:
    for p in processes:
      p.join()
  except KeyboardInterrupt:
    for p in processes:
      p.terminate()
