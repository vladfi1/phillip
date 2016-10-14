import os
import sys
from argparse import ArgumentParser
import subprocess

parser = ArgumentParser()

parser.add_argument('--dry_run', action='store_true', help="don't start jobs")
parser.add_argument('--init', action='store_true', help="initialize model")
parser.add_argument('--trainer', type=str, help='trainer IP address')
parser.add_argument('--local', action='store_true', help="run locally")

args = parser.parse_args()

if not os.path.exists("slurm_logs"):
    os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
    os.makedirs("slurm_scripts")

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

model = 'DQN'
#model = 'NaturalDQN'
#model = 'ActorCriticSplit'
#model = 'RecurrentActorCritic'
#model = 'NaturalActorCritic'

add_param('model', model, both)
#add_param('epsilon', 0.02, both, False)

train_settings = [
  #('optimizer', 'Adam'),
  #('learning_rate', 0.0002),
  ('tdN', 6),
  ('iters', 1),
  ('batch_size', 2),
  ('batch_steps', 2),
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
  add_param('policy_scale', 1, ['train'], True)
  add_param('entropy_scale', 5e-4, ['train'], True)
  #add_param('target_kl', 1e-5, ['train'], True)

if model.count('Natural'):
  if model.count('ActorCritic'):
    add_param('kl_scale', 0.1, ['train'], True)
    
  if True:
    add_param('target_distance', 2e-5, ['train'], True)
    add_param('learning_rate', 1., ['train'], False)
  else:
    add_param('learning_rate', 0.01, ['train'], True)
  
  add_param('cg_damping', 1e-5, ['train'], False)
  add_param('cg_iters', 20, ['train'], False)
else:
  add_param('learning_rate', 0.0001, ['train'], True)

for k, v in train_settings:
  add_param(k, v, ['train'], False)

#add_param('action_space', 

# agent settings

#add_param('dump', args.trainer, ['agent'], False)
add_param('dolphin', True, ['agent'], False)

self_play = False
self_play = 1200
add_param('self_play', self_play, ['agent'], False)

add_param('experience_time', 20, both, False)
add_param('act_every', 3, both, False)
#add_param('delay', 0, ['agent'])
#add_param('memory', 0, both)

#movie = 'movies/endless_netplay_battlefield_dual.dtm'
#add_param('movie', movie, ['agent'], False)

char = 'fox'
add_param('char', char, ['agent'], True)

enemy_table = {
  "nac1" : "agents/nac1/",
}

enemies = [
  "nac1", # fox fox fd
]

exp_name += "_enemies"
for enemy in enemies:
  exp_name += "_" + enemy

job_dicts['enemies'] = enemies

# number of agents playing each enemy
agents = 2
job_dicts['agents'] = agents
print("Launching %d agents." % agents)
agents //= len(enemies)

add_param('name', exp_name, both, False)
path = "saves/%s/" % exp_name
add_param('path', path, both, False)

run_agents = False
run_trainer = False

if args.local:
  add_param('dump', "localhost", ['agent'], False)
  #add_param('dump', "ib0", ['train'], False)
  run_agents = True
  run_trainer = True
else:
  if args.trainer:
    dump = "172.16.24.%s" % args.trainer
    add_param('dump', dump, ['agent'], False)
    run_agents = True
  else:
    add_param('dump', "ib0", ['train'], False)
    run_trainer = True

def slurm_script(name, command, cpus=2, mem=1000, gpu=False, log=True, qos=None, array=None):
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
      subprocess.Popen(command.split(' '), **kwargs)
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
      #f.write("#SBATCH --gres gpu:titan-x:1\n")
      f.write("#SBATCH --gres gpu:1\n")
    if qos:
      f.write("#SBATCH --qos %s\n" % qos)
    if array:
      f.write("#SBATCH --array=1-%d\n" % array)
    f.write(command)

  #command = "screen -S %s -dm srun --job-name %s --pty singularity exec -B $OM_USER/phillip -B $HOME/phillip/ -H ../home phillip.img gdb -ex r --args %s" % (name[:10], name, command)
  os.system("sbatch " + slurmfile)

if args.dry_run:
  print("NOT starting jobs:")
else:
  print("Starting jobs:")

  # init model for the first time
  if args.init:
    import RL
    model = RL.Model(mode=RL.Mode.TRAIN, **job_dicts['train'])
    model.init()
    model.save()
    
    import json
    for k, v in job_dicts.items():
      with open(path + k, 'w') as f:
        json.dump(v, f, indent=2)

if run_trainer:
  train_name = "trainer_" + exp_name
  train_command = "python3 -u train.py" + job_flags['train']
  
  slurm_script(train_name, train_command,
    gpu=True,
    qos='tenenbaum',
    mem=16000
  )

if run_agents:
  agent_count = 0
  agent_command = "python3 -u run.py" + job_flags['agent']
  for enemy in enemies:
    command = agent_command + " --enemy %s" % enemy_table[enemy]

    #for _ in range(agents):
    agent_name = "agent_%d_%s" % (agent_count, exp_name)
    slurm_script(agent_name, command, log=False, array=agents)
    agent_count += 1

