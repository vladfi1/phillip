#!/usr/bin/env python
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
args = parser.parse_args()

if args.tag:
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

model = 'ActorCritic'

exp_name += model

recurrent = True

# add_param('policy', model, False)
add_param('epsilon', 0.005, False)

natural = True
natural = False
#natural = ac

#add_param('optimizer', 'Adam', False)
#add_param('learning_rate', 1e-4, False),
add_param('sweeps', 1, False)
add_param('batch_size', 64, False)
add_param('batch_steps', 1, False)
add_param("max_buffer", 64, False)
add_param('min_collect', 32, False)

add_param('reward_halflife', 4, False)

#add_param('dynamic', 0)

# evolution
evolve = False
#evolve = True

if evolve:
  add_param("evolve", True, False)
  add_param("pop_size", 4)
  add_param("reward_cutoff", 2e-4, False)
  add_param("evo_period", 4000, False)
  add_param("evolve_entropy", True, False)
  add_param("evolve_learning_rate", True, False)
  add_param("reward_decay", 2e-4, False)

# add_param('explore_scale', 1e-4)

delay = 2
predict_steps = 0
#predict_steps = delay

if predict_steps:
  add_param('predict_steps', predict_steps)
  add_param('predict', True, False)
  add_param('model_weight', .1, False)
  add_param('model_layers', [256], False)
  add_param('train_model', True, False)
  # add_param('train_only_last', True, True)

add_param('core_layers', [256], False)
add_param('actor_layers', [128], False)
add_param('critic_layers', [128], False)

#add_param('train_policy', True)
#add_param('train_critic', False)

#add_param('entropy_power', 0)
add_param('entropy_scale', 1e-3, False)

if recurrent:
  # add_param('clip', 0.05)
  add_param('recurrent', True)
  add_param('initial', 'train', False)

add_param('gae_lambda', 1., False)
#add_param('retrace', True)

add_param('unshift_critic', True, True)

# embed params

add_param('xy_scale', 0.05, False)
#add_param('speed_scale

add_param('action_space', 0, False)
add_param('player_space', 0, False)

#add_param('critic_layers', [128] * 1)
#add_param('actor_layers', [128] * 3)
add_param('nl', 'elu', False)

add_param('action_type', 'custom', False)

add_param('fix_scopes', True, False)

# agent settings

#add_param('dolphin', True, False)

add_param('experience_length', 80, False)
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
#char = 'bowser'
#char = 'dk'

from phillip import data
#act_every = 2
act_every = data.short_hop[char]
add_param('act_every', act_every, False)

if delay:
  add_param('delay', delay)
if not recurrent:
  add_param('memory', 1)
  #add_param('memory', 0, False)

stage = 'battlefield'
#stage = 'final_destination'
add_param('stage', stage, False)

add_param('char', char, True)

enemies = None
enemies = "cpu"
#enemies = "easy"
#enemies = "delay0"
#enemies = "delay%d" % delay
#enemies = ['self']
#enemies = 'hard-self'
add_param('enemies', enemies)

add_param('enemy_reload', 3600, False)

# total number of agents
agents = 80
params['agents'] = agents

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
