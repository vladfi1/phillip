import RL
import os

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("--debug", action="store_true",
                   help="set debug breakpoint")
parser.add_argument("-q", "--quiet", action="store_true",
                   help="don't print status messages to stdout")
parser.add_argument("--init", action="store_true",
                   help="initialize variables")

args = parser.parse_args()

if args.init:
  RL.init()
  RL.save()
else:
  RL.restore()

RL.debug = args.debug

def sweep(data_dir='experience/'):
  # for f in ["2"]:
  i = 0
  for f in os.listdir(data_dir):
    if f.isdigit() and f != '0':
        filename = data_dir + f
        print("Step", i)
        print("Experience " + filename)
        RL.train(filename)
        i += 1
    else:
        print("Not training on file:", f)
  RL.save()
  #RL.writeGraph()

while True:
  sweep()
