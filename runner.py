import os
import sys
import subprocess
import util

exp_name = "diagonal"
job_flags = dict(train="", agent="")
job_dicts = dict(train={}, agent={})

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
    flag = " --" + param + " " + str(value)
    for job in jobs:
      job_flags[job] += flag
      job_dicts[job][param] = value
    if name:
      exp_name += "_" + param + "_" + str(value)

both = ['train', 'agent']

#model = 'DQN'
#model = 'NaturalDQN'
model = 'ActorCritic'
#model = 'RecurrentActorCritic'
#model = 'NaturalActorCritic'

add_param('model', model, both)
add_param('epsilon', 0.02, both, False)

add_param('optimizer', 'Adam', ['train'])

train_settings = [
  #('learning_rate', 0.0002),
  ('tdN', 6),
  ('sweeps', 1),
  ('batches', 2),
  ('batch_size', 1),
  ('batch_steps', 1),
  ('gpu', 1),
]

#add_param('learning_rate', 0.001, ['train'], True)

if model.count('DQN'):
  train_settings += [
    ('sarsa', 1),
    #('target_delay', 4000),
  ]
  add_param('temperature', 0.005, ['agent'], True)
elif model.count('ActorCritic'):
  add_param('policy_scale', 0.1, ['train'], True)
  add_param('entropy_scale', 5e-4, ['train'], True)
  #add_param('target_kl', 1e-5, ['train'], True)

natural = True
#natural = False

if natural:
  add_param('natural', True, ['train'], True)
  if model.count('ActorCritic'):
    add_param('kl_scale', 0.1, ['train'], True)
    
  if False:
    add_param('target_distance', 1e-5, ['train'], True)
    add_param('learning_rate', 1., ['train'], False)
  else:
    add_param('learning_rate', 1., ['train'], True)
  
  train_settings += [
    ('cg_damping', 1e-5),
    ('cg_iters', 20),
  ]
else:
  add_param('learning_rate', 0.001, ['train'], True)

for k, v in train_settings:
  add_param(k, v, ['train'], False)

#add_param('action_space', 

# agent settings

add_param('dolphin', True, ['agent'], False)

add_param('experience_time', 5, both, False)
add_param('act_every', 3, both, False)
#add_param('delay', 0, ['agent'])
#add_param('memory', 0, both)

#movie = 'movies/endless_netplay_battlefield_dual.dtm'
#add_param('movie', movie, ['agent'], False)

#char = 'marth'
char = 'fox'
add_param('char', char, ['agent'], True)

enemies = [
  "self",
]

add_param('enemy_reload', 600, ['agent'], False)

exp_name += "_enemies"
for enemy in enemies:
  exp_name += "_" + enemy

job_dicts['enemies'] = enemies

# number of agents playing each enemy
agents = 80
job_dicts['agents'] = agents

add_param('name', exp_name, both, False)
path = "saves/%s/" % exp_name
add_param('path', path, both, False)

print("Writing to", path)
util.makedirs(path)

import json
with open(path + "params", 'w') as f:
  json.dump(job_dicts, f, indent=2)
