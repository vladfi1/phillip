#!/usr/bin/env python

import os
import sys
from argparse import ArgumentParser
import subprocess
from phillip import util
import json
from launch_lib import add_options, launch

parser = ArgumentParser()

parser.add_argument('path', type=str, help="path to enemies file")
add_options(parser)

args = parser.parse_args()

run_trainer_b = True
run_agents_b = True

if args.disk or args.play:
  run_trainer_b = False

if args.dry_run:
  print("NOT starting jobs:")
else:
  print("Starting jobs:")

if not os.path.exists("slurm_logs"):
  os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
  os.makedirs("slurm_scripts")

pids = []

with open(args.path) as f:
  agent_paths = json.load(f)

agent_paths = ['agents/' + e for e in agent_paths]

def get_agents(path):
  params = util.load_params(path)
  pop_size = params.get('pop_size')
  if pop_size and args.pop_size:
    pop_size = min(pop_size, args.pop_size)
  
  if pop_size:
    pop_ids = range(pop_size)
  else:
    pop_ids = [-1]

  return [(path, params, pop_id) for pop_id in pop_ids]

agents = []
for agent_list in map(get_agents, agent_paths):
  agents.extend(agent_list)

trainer_ids = []

def run_trainer(path, params, pop_id):
  name = "trainer_" + params['name']
  command = "python3 -u phillip/train.py --load " + path
  command += " --dump " + ("lo" if args.local else "ib0")
  command += " --send %d" % args.send
  
  if args.init:
    command += " --init"
  
  if pop_id >= 0:
    name += "_%d" % pop_id
    command += " --pop_id %d" % pop_id
    if args.pop_size:
      command += " --pop_size %d" % min(args.pop_size, params['pop_size'])

  trainer_id = launch(
    args, name, command,
    gpu=not args.cpu,
    qos='tenenbaum' if args.tenenbaum else None,
    mem=16,
    pids=pids,
  )
  
  if trainer_id:
    trainer_ids.append(trainer_id)

trainer_depends = None
if run_trainer_b:
  for agent_args in agents:
    run_trainer(*agent_args)
  if trainer_ids:
    trainer_depends = ":".join(trainer_ids)

enemy_commands = []
for enemy_path, _, enemy_id in agents:
  enemy_command = " --enemy %s" % enemy_path
  if enemy_id >= 0:
    enemy_command += " --enemy_id %d" % enemy_id
  enemy_commands.append(enemy_command)

def run_agents(path, params, pop_id):
  actors = args.agents or params.get('agents', 1)

  print("Using %d actors" % actors)
  actors_per_enemy = actors // len(agents)

  common_command = "python3 -u phillip/run.py --load " + path
  if args.disk:
    common_command += " --disk 1"
  else:
    common_command += " --dump 1"

  if run_trainer_b:
    if args.local:
      common_command += " --trainer_ip 127.0.0.1"

  if args.local:
    common_command += " --dual_core 0"
  
  common_command += " --dolphin --exe dolphin-emu-headless"
  common_command += " --zmq 1 --pipe_count 1"
  common_command += " --random_swap"
  # common_command += " --help"
  common_command += " --enemy_dump 1 --enemy_reload 1"

  base_name = "actor_" + params['name']
  if pop_id >= 0:
    base_name += "_%d" % pop_id
    common_command += " --pop_id %d" % pop_id

  for i, enemy_command in enumerate(enemy_commands):
    name = base_name + "_%d" % i
  
    full_command = common_command + enemy_command

    launch(
      args, name, full_command,
      log=args.log_agents,
      qos='use-everything' if args.use_everything else None,
      array=actors_per_enemy,
      depends=trainer_depends,
      pids=pids,
    )

if run_agents_b:
  for agent_args in agents:
    run_agents(*agent_args)

if args.local:
  with open(args.path + '/pids', 'w') as f:
    for p in pids:
      f.write(str(p) + ' ')
