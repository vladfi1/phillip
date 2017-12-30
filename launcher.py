#!/usr/bin/env python

import os
import sys
from argparse import ArgumentParser
import subprocess
from phillip import util
import json

parser = ArgumentParser()

parser.add_argument('path', type=str, help="path to experiment")
parser.add_argument('--dry_run', action='store_true', help="don't start jobs")
parser.add_argument('--init', action='store_true', help="initialize model")
#parser.add_argument('--trainer', type=str, help='trainer IP address')
parser.add_argument('--play', action='store_true', help="run only agents, not trainer")
parser.add_argument('--local', action='store_true', help="run locally")
parser.add_argument('--agents', type=int, help="number of agents to run")
parser.add_argument('--log_agents', action='store_true', help='log agent outputs')
parser.add_argument('--profile', action='store_true', help='heap profile trainer')
parser.add_argument('--disk', action='store_true', help='run agents and dump experiences to disk')
parser.add_argument('-p', '--tenenbaum', action='store_true', help='run trainer on higher priority')
parser.add_argument('-u' ,'--use_everything', action='store_true', help='run agents on lower priority')
parser.add_argument('-g', '--any_gpu', action='store_true', help='run with any gpu (default is titan-x)')
parser.add_argument('-t', '--time', type=str, default="7-0", help='job runtime in days-hours')
parser.add_argument('--nogpu', action='store_true', help="don't run trainer on a gpu")
parser.add_argument('--send', type=int, default=1, help='send params with zmq PUB/SUB')

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

def launch(name, command, cpus=2, mem=1, gpu=False, log=True, qos=None, array=None, depends=None):
  #command = "LD_PRELOAD=$OM_USER/lib/libtcmalloc.so.4 " + command
  if gpu:
    command += " --gpu"
  
  print(command)
  if args.dry_run:
    return
  
  if args.local:
    if array is None:
      array = 1
    for i in range(array):
      kwargs = {}
      for s in ['out', 'err']:
        kwargs['std' + s] = open("slurm_logs/%s_%d.%s" % (name, i, s), 'w') if log else subprocess.DEVNULL
      proc = subprocess.Popen(command.split(' '), **kwargs)
      pids.append(proc.pid)
    return None

  slurmfile = 'slurm_scripts/' + name + '.slurm'
  with open(slurmfile, 'w') as f:
    def opt(s):
      f.write("#SBATCH " + s + "\n")
    f.write("#!/bin/bash\n")
    f.write("#SBATCH --job-name " + name + "\n")
    
    logname = name
    if array:
      logname += "_%a"
    if log:
      f.write("#SBATCH --output slurm_logs/" + logname + ".out\n")
    else:
      f.write("#SBATCH --output /dev/null")
    f.write("#SBATCH --error slurm_logs/" + logname + ".err\n")
    
    f.write("#SBATCH -c %d\n" % cpus)
    f.write("#SBATCH --mem %dG\n" % mem)
    f.write("#SBATCH --time %s\n" % args.time)
    #f.write("#SBATCH --cpu_bind=verbose,cores\n")
    #f.write("#SBATCH --cpu_bind=threads\n")
    opt("--partition=om_all_nodes,om_test_nodes")
    if gpu:
      f.write("#SBATCH --gres gpu:1\n")
      if not args.any_gpu:  # 31-54 have titan-x, 55-66 have 1080ti
        f.write("#SBATCH -x node[001-030]\n")
    if qos:
      f.write("#SBATCH --qos %s\n" % qos)
    if array:
      f.write("#SBATCH --array=1-%d\n" % array)

    if depends:
      opt("--dependency after:" + depends)

    if gpu:
      f.write("source activate tf-gpu-pypi\n")
    else:
      f.write("source activate tf-cpu-pypi\n")
    f.write(command)

  #command = "screen -S %s -dm srun --job-name %s --pty singularity exec -B $OM_USER/phillip -B $HOME/phillip/ -H ../home phillip.img gdb -ex r --args %s" % (name[:10], name, command)
  output = subprocess.check_output(["sbatch", slurmfile]).decode()
  print(output)
  jobid = output.split()[-1].strip()
  return jobid

def get_pop_ids(path):
  agent_params = util.load_params(path)
  agent_pop_size = agent_params.get('pop_size')
  
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
  
    trainer_id = launch(train_name, command,
      gpu=not args.nogpu,
      qos='tenenbaum' if args.tenenbaum else None,
      mem=16,
    )
    
    if trainer_id:
      trainer_ids.append(trainer_id)
  
  trainer_depends = ','.join(trainer_ids)

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
      else:
        enemy_path = "agents/%s/" % enemy
      command += " --enemy " + enemy_path
      
      enemy_ids = get_pop_ids(enemy_path)
      agents_per_enemy2 = agents_per_enemy // len(enemy_ids)
      for pop_id in enemy_ids:
        enemy_commands.append((command + " --enemy_id %d" % pop_id, agents_per_enemy2))
    else: # cpu dict
      command = " --cpu {level} --p1 {char}".format(**enemy)
      enemy_commands.append((command, agent_per_enemy))
  
  for pop_id in pop_ids:
    namer = AgentNamer(params['name'] + "_%d" % pop_id)
    agent_command = common_command
    agent_command += " --pop_id %d" % pop_id
    
    for enemy_command, num_agents in enemy_commands:
      agent_name = namer()
      full_command = agent_command + enemy_command

      launch(agent_name, full_command,
        log=args.log_agents,
        qos='use-everything' if args.use_everything else None,
        array=num_agents,
        depends=trainer_depends,
      )

if args.local:
  with open(args.path + '/pids', 'w') as f:
    for p in pids:
      f.write(str(p) + ' ')
