#!/bin/env python

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

# init model for the first time
if args.init:
  from phillip import RL
  rl = RL.RL(mode=RL.Mode.TRAIN, **params)
  rl.init()
  rl.save()

if not os.path.exists("slurm_logs"):
  os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
  os.makedirs("slurm_scripts")

pids = []

def launch(name, command, cpus=2, mem=1, gpu=False, log=True, qos=None, array=None, depends=None):
  #command = "LD_PRELOAD=$OM_USER/lib/libtcmalloc.so.4 " + command
  if gpu:
    command += " --gpu"
  
  if args.dry_run:
    print(command)
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
    if log:
      f.write("#SBATCH --output slurm_logs/" + name + "_%a.out\n")
    else:
      f.write("#SBATCH --output /dev/null")
    f.write("#SBATCH --error slurm_logs/" + name + "_%a.err\n")
    f.write("#SBATCH -c %d\n" % cpus)
    f.write("#SBATCH --mem %dG\n" % mem)
    f.write("#SBATCH --time %s\n" % args.time)
    #f.write("#SBATCH --cpu_bind=verbose,cores\n")
    #f.write("#SBATCH --cpu_bind=threads\n")
    if gpu:
      if args.any_gpu:
        f.write("#SBATCH --gres gpu:1\n")
      else:
        f.write("#SBATCH --gres gpu:titan-x:1\n")
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

if run_trainer:
  train_name = "trainer_" + params['name']
  train_command = "python3 -u phillip/train.py --load " + args.path
  train_command += " --dump " + ("lo" if args.local else "ib0")
  train_command += " --send %d" % args.send
  
  trainer_id = launch(train_name, train_command,
    gpu=True,
    qos='tenenbaum' if args.tenenbaum else None,
    mem=16
  )
else:
  trainer_id = None

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
  agents //= len(enemies)

  agent_count = 0
  agent_command = "python3 -u phillip/run.py --load " + args.path
  if args.disk:
    agent_command += " --disk 1"
  else:
    agent_command += " --dump 1"

  if run_trainer:
    if trainer_id:
      agent_command += " --trainer_id " + trainer_id
    elif args.local:
      agent_command += " --trainer_ip 127.0.0.1"

  if args.local:
    agent_command += " --dual_core 0"
  
  agent_command += " --dolphin"
  agent_command += " --exe dolphin-emu-headless"
  agent_command += " --zmq 1"
  agent_command += " --pipe_count 1"
  agent_command += " --random_swap"
  # agent_command += " --help"

  for enemy in enemies:
    command = agent_command
    if isinstance(enemy, str):
      command += " --enemy "
      if enemy == "self":
        command += args.path
      else:
        command += "agents/%s/" % enemy
    else: # cpu dict
      command += " --cpu {level} --p1 {char}".format(**enemy)
    
    agent_name = "agent_%d_%s" % (agent_count, params['name'])
    launch(agent_name, command,
      log=args.log_agents,
      qos='use-everything' if args.use_everything else None,
      array=agents,
      depends=trainer_id
    )
    agent_count += 1

if args.local:
  with open(args.path + '/pids', 'w') as f:
    for p in pids:
      f.write(str(p) + ' ')
