#!/usr/bin/env python

import os
import sys
from argparse import ArgumentParser
import subprocess
from phillip import util
import json
from launch_lib import launch, add_options

parser = ArgumentParser()

parser.add_argument('path', type=str, help="path to experiment")
add_options(parser)

args = parser.parse_args()
params = util.load_params(args.path)

run_trainer = True
run_agents = True

if args.disk or args.play:
  run_trainer = False

if args.dry_run:
  print("NOT starting jobs:")
else:
  print("Starting jobs:")

if not os.path.exists("slurm_logs"):
  os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
  os.makedirs("slurm_scripts")

pids = []

def get_pop_ids(path):
  agent_params = util.load_params(path)
  agent_pop_size = args.pop_size or agent_params.get('pop_size')
  
  if agent_pop_size:
    return list(range(agent_pop_size))
  else:
    return [-1]

pop_ids = get_pop_ids(args.path)

trainer_depends = None

if run_trainer:
  common_name = "trainer_" + params['name']
  train_command = "python3 -u phillip/train.py --load " + args.path
  train_command += " --dump " + ("lo" if args.local else "ib0")
  train_command += " --send %d" % args.send
  
  if args.init:
    train_command += " --init"
  
  trainer_ids = []
  
  for pop_id in pop_ids:
    train_name = common_name
    if pop_id >= 0:
      train_name += "_%d" % pop_id
    
    command = train_command
    command += " --pop_id %d" % pop_id
  
    trainer_id = launch(args, train_name, command,
      gpu=not args.cpu,
      qos='tenenbaum' if args.tenenbaum else None,
      mem=16,
      cpus=4,
      pids=pids,
    )
    
    if trainer_id:
      trainer_ids.append(trainer_id)
  
  trainer_depends = ':'.join(trainer_ids)

class AgentNamer:
  def __init__(self, name):
    self.name = name
    self.counter = 0
  
  def __call__(self):
    self.counter += 1
    return "agent_%d_%s" % (self.counter, self.name)

if run_agents:
  enemies = 'easy'
  if 'enemies' in params:
    enemies = params['enemies']

  if isinstance(enemies, str):
    with open('enemies/' + enemies) as f:
      enemies = json.load(f)

  agents = 1
  if params['agents']:
    agents = params['agents']
  if args.agents:
    agents = args.agents

  print("Using %d agents" % agents)
  agents_per_enemy = agents // len(enemies)

  common_command = "python3 -u phillip/run.py --load " + args.path
  if args.disk:
    common_command += " --disk 1"
  else:
    common_command += " --dump 1"

  if run_trainer:
    if args.local:
      common_command += " --trainer_ip 127.0.0.1"

  if args.local:
    common_command += " --dual_core 0"
  
  common_command += " --dolphin"
  common_command += " --exe dolphin-emu-headless"
  common_command += " --zmq 1 --pipe_count 1"
  common_command += " --random_swap"
  # common_command += " --help"
  
  enemy_commands = []
  
  for enemy in enemies:
    if isinstance(enemy, str):
      command = ""
      if enemy == "self":
        enemy_path = args.path
        if not args.fixed_enemy:
          command += " --enemy_dump 1 --enemy_reload 1"
      else:
        enemy_path = "agents/%s/" % enemy
      command += " --enemy " + enemy_path
      
      enemy_ids = get_pop_ids(enemy_path)
      agents_per_enemy2 = agents_per_enemy // len(enemy_ids)
      for pop_id in enemy_ids:
        enemy_commands.append((command + " --enemy_id %d" % pop_id, agents_per_enemy2))
    else: # cpu dict
      command = " --cpu {level} --p1 {char}".format(**enemy)
      enemy_commands.append((command, agents_per_enemy))
  
  for pop_id in pop_ids:
    namer = AgentNamer(params['name'] + "_%d" % pop_id)
    agent_command = common_command
    agent_command += " --pop_id %d" % pop_id
    
    for enemy_command, num_agents in enemy_commands:
      agent_name = namer()
      full_command = agent_command + enemy_command

      launch(args, agent_name, full_command,
        log=args.log_agents,
        qos='use-everything' if args.use_everything else None,
        array=num_agents,
        depends=trainer_depends,
        pids=pids,
      )

if args.local:
  with open(args.path + '/pids', 'w') as f:
    for p in pids:
      f.write(str(p) + ' ')
