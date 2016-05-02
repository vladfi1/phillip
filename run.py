#!/usr/bin/env python3
from argparse import ArgumentParser
parser = ArgumentParser()

parser.add_argument("--name", type=str,
                    help="filename to import from and save to")

parser.add_argument("--nodump", dest='dump', action="store_false",
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
