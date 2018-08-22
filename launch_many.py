#!/usr/bin/env python

import os
import sys
from argparse import ArgumentParser
import subprocess
from phillip import util
import json

parser = ArgumentParser()

parser.add_argument('path', type=str, help="path to enemies file")
parser.add_argument('--dry_run', action='store_true', help="don't start jobs")
parser.add_argument('--init', action='store_true', help="initialize model")
#parser.add_argument('--trainer', type=str, help='trainer IP address')
parser.add_argument('--play', action='store_true', help="run only agents, not trainer")
parser.add_argument('--local', action='store_true', help="run locally")
parser.add_argument('--actors', type=int, help="number of actors to run per trainer")
parser.add_argument('--log_agents', action='store_true', help='log agent outputs')
parser.add_argument('--profile', action='store_true', help='heap profile trainer')
parser.add_argument('--disk', action='store_true', help='run agents and dump experiences to disk')
parser.add_argument('-p', '--tenenbaum', action='store_true', help='run trainer on higher priority')
parser.add_argument('-u' ,'--use_everything', action='store_true', help='run agents on lower priority')
parser.add_argument('-g', '--any_gpu', action='store_true', help='run with any gpu (default is titan-x)')
parser.add_argument('-t', '--time', type=str, default="7-0", help='job runtime in days-hours')
parser.add_argument('--cpu', action='store_true', help="don't run trainer on a gpu")
parser.add_argument('--gpu', type=str, default='GEFORCEGTX1080TI', help='gpu type')
parser.add_argument('--send', type=int, default=1, help='send params with zmq PUB/SUB')
parser.add_argument('--pop_size', type=int, help='max pop size')

args = parser.parse_args()

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
    opt("--job-name " + name)
    
    logname = name
    if array:
      logname += "_%a"
    if log:
      f.write("#SBATCH --output slurm_logs/" + logname + ".out\n")
    else:
      f.write("#SBATCH --output /dev/null\n")
    f.write("#SBATCH --error slurm_logs/" + logname + ".err\n")
    
    f.write("#SBATCH -c %d\n" % cpus)
    f.write("#SBATCH --mem %dG\n" % mem)
    f.write("#SBATCH --time %s\n" % args.time)
    #f.write("#SBATCH --cpu_bind=verbose,cores\n")
    #f.write("#SBATCH --cpu_bind=threads\n")
    #opt("--partition=om_all_nodes,om_test_nodes")
    if gpu:
      if args.any_gpu:
        f.write("#SBATCH --gres gpu:1\n")
      else:
        opt("--gres gpu:%s:1" % args.gpu)
      #if not args.any_gpu:  # 31-54 have titan-x, 55-66 have 1080ti
      #  f.write("#SBATCH -x node[001-030]\n")
    if qos:
      f.write("#SBATCH --qos %s\n" % qos)
    if array:
      f.write("#SBATCH --array=1-%d\n" % array)

    if depends:
      opt("--dependency after:" + depends)

    if gpu:
      opt("-x node069,node067")
      f.write("source ~/.cuda\n")
      f.write("source activate tf-gpu-src\n")
    else:
      f.write("source activate tf-cpu-opt\n")
      f.write("sleep 40s\n")
    f.write(command)

  #command = "screen -S %s -dm srun --job-name %s --pty singularity exec -B $OM_USER/phillip -B $HOME/phillip/ -H ../home phillip.img gdb -ex r --args %s" % (name[:10], name, command)
  output = subprocess.check_output(["sbatch", slurmfile]).decode()
  print(output)
  jobid = output.split()[-1].strip()
  return jobid

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

  trainer_id = launch(name, command,
    gpu=not args.cpu,
    qos='tenenbaum' if args.tenenbaum else None,
    mem=16,
  )
  
  if trainer_id:
    trainer_ids.append(trainer_id)

trainer_depends = None
if run_trainer:
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
  actors = args.actors or params.get('agents', 1)

  print("Using %d actors" % actors)
  actors_per_enemy = actors // len(agents)

  common_command = "python3 -u phillip/run.py --load " + path
  if args.disk:
    common_command += " --disk 1"
  else:
    common_command += " --dump 1"

  if run_trainer:
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

    launch(name, full_command,
      log=args.log_agents,
      qos='use-everything' if args.use_everything else None,
      array=actors_per_enemy,
      depends=trainer_depends,
    )

if run_agents:
  for agent_args in agents:
    run_agents(*agent_args)

if args.local:
  with open(args.path + '/pids', 'w') as f:
    for p in pids:
      f.write(str(p) + ' ')
