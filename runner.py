import os
import sys
import subprocess
from phillip import util
from collections import OrderedDict
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument("--tag", action="store_true", help="generate random tag for this experiment")
parser.add_argument("--name", type=str, help="experiment name")
parser.add_argument("--prefix", type=str, help="experiment prefix")
args = parser.parse_args()

if args.prefix:
  exp_name = args.prefix + "_"
elif args.tag:
  exp_name = str(random.getrandbits(32)) + "_"
else:
  exp_name = ""
params = OrderedDict()

def toStr(val):
  if isinstance(val, list):
    return "_".join(map(str, val))
  return str(val)

def add_param(param, value, name=True):
  global exp_name
  if name and value:
    if isinstance(value, bool):
      exp_name += "_" + param
    else:
      exp_name += "_" + param + "_" + toStr(value)
  params[param] = value

#model = 'DQN'
model = 'RecurrentDQN'
#model = 'ActorCritic'
#model = 'RecurrentActorCritic'

exp_name += model

ac = model.count('RecurrentActorCritic')
dqn = model.count('RecurrentDQN')
#dqn = model.count('DQN')
#ac = model.count('ActorCritic')

add_param('policy', model, False)
add_param('epsilon', 0.02, False)

#natural = True
natural = False
#natural = ac

train_settings = [
  #('learning_rate', 0.0002),
  ('tdN', 20),
  ('reward_halflife', 2),
  ('sweeps', 1),
  ('batches', 1 if natural else 5),
  ('batch_size', 2000),
  ('batch_steps', 1),
]

if dqn:
  train_settings += [
    ('sarsa', 1),
    #('target_delay', 4000),
  ]
  add_param('temperature', 0.002)
elif ac:
  #add_param('entropy_power', 0)
  add_param('entropy_scale', 2e-4)

if natural:
  add_param('natural', True, False)
  
  if ac:
    add_param('target_distance', 1e-6)
  elif dqn:
    add_param('target_distance', 1e-8)
  
  add_param('learning_rate', 1., False)
  
  train_settings += [
    ('cg_damping', 1e-5),
  ]
  add_param('cg_iters', 15, False)
  #add_param('optimizer', 'Adam', True)
else:
  add_param('learning_rate', 1e-4)
  add_param('optimizer', 'Adam', False)

#if recurrent:
#  add_param('clip', 0.05)

for k, v in train_settings:
  if (k == 'reward_halflife'):
    add_param(k, v)
  else:
    add_param(k, v, False)

# embed params

add_param('xy_scale', 0.05, False)
#add_param('speed_scale

add_param('action_space', 0, False)
add_param('player_space', 0, False)

#add_param('critic_layers', [128] * 1)
#add_param('actor_fc_layers', [128] * 2)
#add_param('actor_rnn_layers', [128] * 1)
add_param('q_fc_layers', [128] * 2)
add_param('q_rnn_layers', [128] * 1)
add_param('nl', 'elu')

add_param('initial', 'zero')

add_param('action_type', 'custom', False)

add_param('fix_scopes', True, False)

# agent settings

#add_param('dolphin', True, False)

#add_param('experience_length', 40 + params['tdN'], False)
add_param('experience_length', 60, False)

add_param('reload', 1, False)

#char = 'falco'
#char = 'sheik'
char = 'falcon'
#char = 'marth'
#char = 'fox'
#char = 'peach'
#char = 'luigi'
#char = 'samus'
#char = 'ganon'
#char = 'puff'

from phillip import data
#act_every = 2
act_every = data.short_hop[char]
add_param('act_every', act_every)#, False)

delay = 1
if delay:
  add_param('delay', delay)

stage = 'battlefield'
#stage = 'final_destination'
add_param('stage', stage)

add_param('char', char)

#enemies = None
enemies = "cpu"
#enemies = "easy"
#enemies = "delay0"
#enemies = "delay%d" % delay
#enemies = ['delay0']

add_param('enemies', enemies)

add_param('enemy_reload', 3600, False)

# total number of agents
agents = 160
add_param('agents', agents)

if args.name is not None:
  exp_name = args.name

add_param('name', exp_name, False)
path = "saves/%s/" % exp_name
#add_param('path', path, False)

print("Writing to", path)
util.makedirs(path)

import json
with open(path + "params", 'w') as f:
  json.dump(params, f, indent=2)
