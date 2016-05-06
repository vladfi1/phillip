#!/usr/bin/env python3
from argparse import ArgumentParser
parser = ArgumentParser()

parser.add_argument("--name", type=str,
                    help="filename to import from and save to")

parser.add_argument("--tag", type=str,
                    help="optional tag to mark experiences")

parser.add_argument("--nodump", dest='dump', action="store_false",
                    help="don't dump experiences to disk")

parser.add_argument("--dump_dir", type=str,
                    help="where to dump experiences")

parser.add_argument("--dump_max", type=int,
                   help="caps number of experiences")

parser.add_argument("--dolphin_dir", type=str,
                   help="dolphin user directory")

parser.add_argument("--run_dolphin", action="store_true", help="run dolphin")
parser.add_argument("--setup_dolphin", action="store_true", help="create dolphin dir")

args = parser.parse_args()

p=None

if args.run_dolphin:
  from run_parallel import runDolphin
  p = runDolphin(user=args.dolphin_dir, setup=args.setup_dolphin)

from cpu import CPU
cpu = CPU(**args.__dict__)
cpu.run(dolphin_process=p)
