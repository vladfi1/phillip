import os
import time
import RL
import util

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("--debug", action="store_true", help="set debug breakpoint")
parser.add_argument("-q", "--quiet", action="store_true", help="don't print status messages to stdout")
parser.add_argument("--init", action="store_true", help="initialize variables")
parser.add_argument("--path", help="where to import from and save to")
parser.add_argument("--name", type=str, help="sets path to saves/{name}")
parser.add_argument("--model", choices=RL.models.keys(), required=True, help="which RL model to use")
parser.add_argument("--sarsa", action="store_true", help="learn Q values for the current policy, not the optimal policy")

parser.add_argument("--optimizer", type=str, default="GradientDescent", help="tf.train optimizer")
parser.add_argument("--learning_rate", type=float, default=1e-4, help="optimizer learning rate")
parser.add_argument("--target_kl", type=float, help="target kl divergence for policy gradient methods")

parser.add_argument("--nogpu", dest="gpu", action="store_false", help="don't train on gpu")

parser.add_argument("--tdN", type=int, default=5, help="use n-step TD error")
parser.add_argument("--reward_halflife", type=float, default=2.0, help="time to discount rewards by half, in seconds")

parser.add_argument("--target_delay", type=int, default=5000, help="update target network after this many experiences")

parser.add_argument("--entropy_scale", type=float, default=1e-2, help="entropy regularization for actor-critic")
parser.add_argument("--policy_scale", type=float, default=1.0, help="scale the policy gradient for actor-critic")

parser.add_argument("--iters", type=int, default=1, help="number of iterations between saves")
parser.add_argument("--batch_size", type=int, default=1, help="number of experiences to train on per iteration")
parser.add_argument("--batch_steps", type=int, default=1, help="number of gradient steps to take on each batch")

parser.add_argument("--epsilon", type=float, default=0.04, help="probability of random action")
#parser.add_argument("--temperature", type=float, default=0.01, help="increases action randomness")

# duplicated?
parser.add_argument("--act_every", type=int, default=3, help="only take actions every ACT_EVERY frames")
parser.add_argument("--memory", type=int, default=0, help="how many frames to remember")
parser.add_argument("--experience_time", type=int, default=60, help="length of experiences, in seconds")

args = parser.parse_args()

if args.name is None:
  args.name = args.model

if args.path is None:
  args.path = "saves/%s/" % args.name

model = RL.Model(mode=RL.Mode.TRAIN, **args.__dict__)

# do this in RL?
if args.init:
  model.init()
  model.save()
else:
  model.restore()

import zmq

context = zmq.Context()

socket = context.socket(zmq.PULL)
sock_addr = util.sockAddr(args.name)
print("Binding to " + sock_addr)
socket.bind(sock_addr)

import numpy as np

def sweep():
  start_time = time.time()
  
  for _ in range(args.iters):
    experiences = []
    
    for _ in range(args.batch_size):
      experiences.append(socket.recv_pyobj())
    
    model.train(experiences, **args.__dict__)
  
  total_time = time.time() - start_time
  print("time, experiences", total_time, args.iters * args.batch_size)
  model.save()
  # import pdb; pdb.set_trace()

while True:
  sweep()

