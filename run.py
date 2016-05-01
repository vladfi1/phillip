#!/usr/bin/env python3
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("--name", default='simpleDQN',
                   help="filename to import from and save to")

args = parser.parse_args()

from cpu import CPU
CPU(name=args.name, act_every=5, dump_max=1000).run()
