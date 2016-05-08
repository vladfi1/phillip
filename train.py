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
parser.add_argument("--name", default='simpleDQN',
                   help="filename to import from and save to")

args = parser.parse_args()

experience_dir = 'saves/' + args.name + '/experience/'
os.makedirs(experience_dir, exist_ok=True)

if args.init:
    RL.init()
    RL.save(args.name)
else:
    RL.restore(args.name)

RL.debug = args.debug

def sweep(data_dir='experience/'):
    i = 0
    rewards = []
    for f in os.listdir(data_dir):
        if not f.startswith("."):
            filename = data_dir + f
            print("Step", i)
            print("Experience " + filename)
            rewards.append(RL.train(filename))
            i += 1
        else:
            print("Not training on file:", f)
        print("")
    RL.save(args.name)
    #RL.writeGraph()
    # import pdb; pdb.set_trace()
    mean_reward = sum(rewards) / len(rewards) if len(rewards) > 0 else 0
    return mean_reward

while True:
    sweep(experience_dir)
