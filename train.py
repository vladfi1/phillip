import os
import time

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("--debug", action="store_true",
                   help="set debug breakpoint")
parser.add_argument("-q", "--quiet", action="store_true",
                   help="don't print status messages to stdout")
parser.add_argument("--init", action="store_true",
                   help="initialize variables")
parser.add_argument("--path", help="where to import from and save to")
parser.add_argument("--name", type=str, help="sets path to saves/{name}")
parser.add_argument("--model", choices=["DQN", "ActorCritic"], required=True, help="which RL model to use")
parser.add_argument("--sarsa", action="store_true", help="learn Q values for the current policy, not the optimal policy")

parser.add_argument("--learning_rate", type=float, default=1e-4, help="gradient descent learning rate")

args = parser.parse_args()

if args.name is None:
  args.name = args.model

if args.path is None:
  args.path = "saves/%s/" % args.name

experience_dir = args.path + 'experience/'
os.makedirs(experience_dir, exist_ok=True)

import RL
model = RL.Model(**args.__dict__)

# do this in RL?
if args.init:
    model.init()
    model.save()
else:
    model.restore()

def sweep(data_dir='experience/'):
    i = 0
    rewards = []
    start_time = time.time()
    for f in os.listdir(data_dir):
        if not (f.startswith(".") or f.startswith("tmp")): # .DS_Store, temp files
            filename = data_dir + f
            if not os.path.exists(filename):
                continue
            print("Step", i)
            print("Experience " + filename)
            rewards.append(model.train(filename))
            i += 1
        else:
            print("Not training on file:", f)
        print("")
    if i > 0:
        total_time = time.time() - start_time
        print("time/experience", total_time / i)
    model.save()
    #RL.writeGraph()
    # import pdb; pdb.set_trace()
    mean_reward = sum(rewards) / len(rewards) if len(rewards) > 0 else 0
    return mean_reward

while True:
    sweep(experience_dir)
