#!/usr/bin/env python3
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--no_dump", action="store_false", dest="dump",
                    help="don't dump experiences to disk")

parser.add_argument("--dump_dir", type=str,
                    help="where to dump experiences")

parser.add_argument("--dump_max", type=int,
                   help="caps number of experiences")

parser.add_argument("--dolphin_dir", type=str,
                   help="dolphin user directory")

args = parser.parse_args()

from cpu import CPU
CPU(**args.__dict__).run()
