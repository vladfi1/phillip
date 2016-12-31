import os
import sys
import subprocess
import util
from collections import OrderedDict

exp_name = "diagonal"
job_flags = dict(train="", agent="")
job_dicts = dict(train=OrderedDict(), agent=OrderedDict())

def toStr(val):
  if isinstance(val, list):
    return "_".join(map(str, val))
  return str(val)

def add_param(param, value, jobs, name=True):
  global exp_name
  if isinstance(value, bool):
    if value:
      flag = " --" + param
      for job in jobs:
        job_flags[job] += flag
        job_dicts[job][param] = value
      if name:
        exp_name += "_" + param
  else:
    flag = " --" + param + " " + toStr(value)
    for job in jobs:
      job_flags[job] += flag
      job_dicts[job][param] = value
    if name:
      exp_name += "_" + param + "_" + toStr(value)

both = ['train', 'agent']

#model = 'DQN'
#model = 'ActorCritic'
model = 'RecurrentActorCritic'
#model = 'NaturalActorCritic'

recurrent = model.count('Recurrent')

add_param('model', model, both)
add_param('epsilon', 0.02, both, False)

natural = True
#natural = False

train_settings = [
  #('learning_rate', 0.0002),
  ('tdN', 5),
  ('sweeps', 1),
  ('batches', 2 if recurrent else 10),
  ('batch_size', 1000 if recurrent else 2000),
  ('batch_steps', 1),
  ('gpu', 1),
]

if model.count('DQN'):
  train_settings += [
    ('sarsa', 1),
    #('target_delay', 4000),
  ]
  add_param('temperature', 0.002, both)
elif model.count('ActorCritic'):
  add_param('entropy_power', 0, ['train'])
  if natural:
    add_param('entropy_scale', 1e-4, ['train'], True)
  else:
    add_param('entropy_scale', 1e-3 if recurrent else 3e-3, ['train'], True)

if natural:
  add_param('natural', True, ['train'], True)
  
  if True:
    add_param('target_distance', 1e-6, ['train'], True)
    add_param('learning_rate', 1., ['train'], False)
  else:
    add_param('learning_rate', 1., ['train'], True)
  
  train_settings += [
    ('cg_damping', 1e-5),
  ]
  add_param('cg_iters', 10, ['train'], True)
  #add_param('optimizer', 'Adam', ['train'], True)
else:
  add_param('learning_rate', 1e-5 if recurrent else 1e-4, ['train'], True)
  add_param('optimizer', 'Adam', ['train'], False)

#if recurrent:
#  add_param('clip', 0.05, ['train'])

for k, v in train_settings:
  add_param(k, v, ['train'], False)

# embed params

add_param('xy_scale', 0.05, both, False)
#add_param('speed_scale

add_param('action_space', 0, both, False)
add_param('player_space', 0, both, False)

#add_param('critic_layers', [128] * 1, both)
#add_param('actor_layers', [128] * 3, both)

# agent settings

add_param('dolphin', True, ['agent'], False)

add_param('experience_time', 1 if recurrent else 2, both, False)
add_param('reload', 2, ['agent'], False)
add_param('act_every', 2, both, False)

delay = 8
if delay:
  add_param('delay', delay, both)
if not recurrent:
  add_param('memory', 1 + delay, both)

#movie = 'movies/endless_netplay_battlefield_dual.dtm'
#add_param('movie', movie, ['agent'], False)

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
add_param('char', char, ['agent'], True)

#enemies = "easy"
enemies = "delay2"
#enemies = "delay%d" % delay
add_param('enemy_reload', 600, ['agent'], False)

exp_name += "_enemies_" + enemies
job_dicts['enemies'] = enemies

# number of agents playing each enemy
agents = 60
job_dicts['agents'] = agents

add_param('name', exp_name, both, False)
path = "saves/%s/" % exp_name
#add_param('path', path, both, False)

print("Writing to", path)
util.makedirs(path)

import json
with open(path + "params", 'w') as f:
  json.dump(job_dicts, f, indent=2)
