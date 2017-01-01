import os
import sys
import subprocess
import util
from collections import OrderedDict

exp_name = "diagonal"
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
#model = 'ActorCritic'
model = 'RecurrentActorCritic'
#model = 'NaturalActorCritic'

recurrent = model.count('Recurrent')

add_param('model', model)
add_param('epsilon', 0.02, False)

natural = True
#natural = False

train_settings = [
  #('learning_rate', 0.0002),
  ('tdN', 5),
  ('sweeps', 1),
  ('batches', 1 if recurrent else 10),
  ('batch_size', 1000 if recurrent else 2000),
  ('batch_steps', 1),
  ('gpu', 1),
]

if model.count('DQN'):
  train_settings += [
    ('sarsa', 1),
    #('target_delay', 4000),
  ]
  add_param('temperature', 0.002)
elif model.count('ActorCritic'):
  add_param('entropy_power', 0)
  if natural:
    add_param('entropy_scale', 1e-4, True)
  else:
    add_param('entropy_scale', 1e-3 if recurrent else 3e-3, True)

if natural:
  add_param('natural', True, True)
  
  if True:
    add_param('target_distance', 1e-6, True)
    add_param('learning_rate', 1., False)
  else:
    add_param('learning_rate', 1., True)
  
  train_settings += [
    ('cg_damping', 1e-5),
  ]
  add_param('cg_iters', 10, True)
  #add_param('optimizer', 'Adam', True)
else:
  add_param('learning_rate', 1e-5 if recurrent else 1e-4, True)
  add_param('optimizer', 'Adam', False)

#if recurrent:
#  add_param('clip', 0.05)

for k, v in train_settings:
  add_param(k, v, False)

# embed params

add_param('xy_scale', 0.05, False)
#add_param('speed_scale

add_param('action_space', 0, False)
add_param('player_space', 0, False)

#add_param('critic_layers', [128] * 1)
#add_param('actor_layers', [128] * 3)

# agent settings

add_param('dolphin', True, False)

add_param('experience_time', 1 if recurrent else 2, False)
add_param('reload', 2, False)
add_param('act_every', 2, False)

delay = 8
if delay:
  add_param('delay', delay)
if not recurrent:
  add_param('memory', 1 + delay)

#movie = 'movies/endless_netplay_battlefield_dual.dtm'
#add_param('movie', movie, False)

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
add_param('char', char, True)

#enemies = "easy"
enemies = "delay2"
#enemies = "delay%d" % delay
add_param('enemy_reload', 600, False)

exp_name += "_enemies_" + enemies
params['enemies'] = enemies

# number of agents playing each enemy
agents = 60
params['agents'] = agents

add_param('name', exp_name, False)
path = "saves/%s/" % exp_name
#add_param('path', path, False)

print("Writing to", path)
util.makedirs(path)

import json
with open(path + "params", 'w') as f:
  json.dump(params, f, indent=2)
