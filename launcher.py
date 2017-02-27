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
parser.add_argument('--trainer', type=str, help='trainer IP address')
parser.add_argument('--local', action='store_true', help="run locally")
parser.add_argument('--agents', type=int, help="number of agents to run")
parser.add_argument('--log_agents', action='store_true', help='log agent outputs')
parser.add_argument('--profile', action='store_true', help='heap profile trainer')

args = parser.parse_args()


params = util.load_params(args.path)

run_trainer = True
run_agents = True

if args.local:
  agent_dump = "localhost"
  trainer_dump = "127.0.0.1"
else: # running on openmind
  if args.trainer:
    agent_dump = "172.16.24.%s" % args.trainer
    run_trainer = False
  else:
    trainer_dump = "ib0"
    run_agents = False

if args.dry_run:
  print("NOT starting jobs:")
else:
  print("Starting jobs:")

# init model for the first time
if args.init:
  from phillip import RL
  model = RL.Model(mode=RL.Mode.TRAIN, **params)
  model.init()
  model.save()

if not os.path.exists("slurm_logs"):
  os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
  os.makedirs("slurm_scripts")

pids = []

def launch(name, command, cpus=2, mem=1000, gpu=False, log=True, qos=None, array=None):
  #command = "LD_PRELOAD=$OM_USER/lib/libtcmalloc.so.4 " + command
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
    return

  slurmfile = 'slurm_scripts/' + name + '.slurm'
  with open(slurmfile, 'w') as f:
    f.write("#!/bin/bash\n")
    f.write("#SBATCH --job-name " + name + "\n")
    if log:
      f.write("#SBATCH --output slurm_logs/" + name + "_%a.out\n")
      f.write("#SBATCH --error slurm_logs/" + name + "_%a.err\n")
    else:
      f.write("#SBATCH --output /dev/null")
      f.write("#SBATCH --error /dev/null")
    f.write("#SBATCH -c %d\n" % cpus)
    f.write("#SBATCH --mem %d\n" % mem)
    f.write("#SBATCH --time 7-0\n")
    #f.write("#SBATCH --cpu_bind=verbose,cores\n")
    #f.write("#SBATCH --cpu_bind=threads\n")
    if gpu:
      f.write("#SBATCH --gres gpu:titan-x:1\n")
      #f.write("#SBATCH --gres gpu:1\n")
    if qos:
      f.write("#SBATCH --qos %s\n" % qos)
    if array:
      f.write("#SBATCH --array=1-%d\n" % array)
    f.write(command)

  #command = "screen -S %s -dm srun --job-name %s --pty singularity exec -B $OM_USER/phillip -B $HOME/phillip/ -H ../home phillip.img gdb -ex r --args %s" % (name[:10], name, command)
  os.system("sbatch " + slurmfile)

if run_trainer:
  train_name = "trainer_" + params['name']
  train_command = "python3 -u phillip/train.py --load " + args.path
  train_command += " --dump " + trainer_dump

  if not args.local: # TODO: support LD_PRELOAD for local args too
    if args.profile:
      env_vars = "LD_PRELOAD=$OM_USER/lib/libtcmalloc.so HEAPPROFILE=profile/%s " % train_name
    else:
      env_vars = "LD_PRELOAD=$OM_USER/lib/libtcmalloc_minimal.so "
  
    train_command = env_vars + train_command

  launch(train_name, train_command,
    gpu=True,
    qos='tenenbaum',
    mem=16000
  )

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
  agent_command = "phillip --load " + args.path
  agent_command += " --dump " + agent_dump
  agent_command += " --listen " + agent_dump
  if not args.local:
    agent_command += " --cpu_thread"
  
  agent_command += " --dolphin"
  agent_command += " --exe dolphin-emu-headless"
  agent_command += " --zmq 1"
  agent_command += " --pipe_count 1"

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
      qos='use-everything',
      array=agents
    )
    agent_count += 1

if args.local:
  with open(args.path + '/pids', 'w') as f:
    for p in pids:
      f.write(str(p) + ' ')
