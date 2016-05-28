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
parser.add_argument("--model", choices=["DQN", "ActorCritic", "ThompsonDQN"], required=True, help="which RL model to use")
parser.add_argument("--sarsa", action="store_true", help="learn Q values for the current policy, not the optimal policy")

parser.add_argument("--learning_rate", type=float, default=1e-4, help="gradient descent learning rate")

parser.add_argument("--nogpu", action="store_true", help="don't train on gpu")

parser.add_argument("--tdN", type=int, default=5, help="use n-step TD error")
parser.add_argument("--reward_halflife", type=float, default=2.0, help="time to discount rewards by half, in seconds")

parser.add_argument("--target_delay", type=int, default=5000, help="update target network after this many experiences")

parser.add_argument("--entropy_scale", type=float, default=1e-2, help="entropy regularization for actor-critic")

args = parser.parse_args()

if args.nogpu:
  os.environ["CUDA_VISIBLE_DEVICES"] = ""

if args.name is None:
  args.name = args.model

if args.path is None:
  args.path = "saves/%s/" % args.name

experience_dir = args.path + 'experience/'
os.makedirs(experience_dir, exist_ok=True)

import RL
model = RL.Model(mode=RL.Mode.TRAIN, **args.__dict__)

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
