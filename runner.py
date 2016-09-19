import os
import sys
from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument('--dry_run', action='store_true', help="don't start jobs")
parser.add_argument('--init', action='store_true', help="initialize model")
parser.add_argument('--trainer', type=str, help='trainer IP address')

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
model = 'ActorCriticSplit'
#model = 'RecurrentActorCritic'
add_param('model', model, both)
#add_param('model', 'ActorCriticSplit', both)
add_param('epsilon', 0.02, both, False)

train_settings = [
  ('optimizer', 'Adam'),
  ('learning_rate', 0.001),
  ('tdN', 5),
  ('iters', 1),
  ('batch_size', 10),
  ('batch_steps', 1),
]

if model.count('DQN'):
  train_settings += [
    ('sarsa', True),
    ('target_delay', 4000),
  ]
  add_param('temperature', 0.002, ['agent'])
elif model.count('ActorCritic'):
  add_param('policy_scale', 5e-2, ['train'], True)
  add_param('entropy_scale', 1e-3, ['train'], True)
  add_param('target_kl', 5e-5, ['train'], True)

for k, v in train_settings:
  add_param(k, v, ['train'], False)

# agent settings

add_param('dump', args.trainer, ['agent'], False)
add_param('dolphin', True, ['agent'], False)

# number of agents playing each matchup
agents = 9
add_param('agents', agents, [], False)

self_play = False
self_play = 720
add_param('self_play', self_play, ['agent'], False)

add_param('experience_time', 10, both, False)
add_param('act_every', 3, both)
add_param('delay', 0, ['agent'])
add_param('memory', 0, both, False)

#movie = 'movies/endless_netplay_battlefield_dual.dtm'
#add_param('movie', movie, ['agent'], False)

characters = [
  'fox',
#  'zelda',
  'marth',
#  'roy',
  'falcon',
]

for c in characters:
  exp_name += '_' + c

add_param('name', exp_name, both, False)
add_param('path', "saves/%s/" % exp_name, both, False)

def slurm_script(name, command, cpus=2, mem=1000, gpu=False, log=True, qos=None, array=None):
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
    f.write("#SBATCH --time 6-23\n")
    #f.write("#SBATCH --cpu_bind=verbose,cores\n")
    #f.write("#SBATCH --cpu_bind=threads\n")
    if gpu:
      f.write("#SBATCH --gres gpu:titan-x:1\n")
    if qos:
      f.write("#SBATCH --qos %s\n" % qos)
    if array:
      f.write("#SBATCH --array=1-%d\n" % array)
    f.write(command)

  #command = "screen -S %s -dm srun --job-name %s --pty singularity exec -B $OM_USER/phillip -B $HOME/phillip/ -H ../home phillip.img gdb -ex r --args %s" % (name[:10], name, command)

  if args.dry_run:
    print(command)
  else:
    #os.system(command)
    os.system("sbatch " + slurmfile)
    #os.system("sbatch -N 1 -c 2 --mem=8000 --time=6-23:00:00 slurm_scripts/" + jobname + ".slurm &")

if args.dry_run:
  print("NOT starting jobs:")
else:
  print("Starting jobs:")

  # init model for the first time
  if args.init:
    import RL
    model = RL.Model(mode=RL.Mode.TRAIN, gpu=False, **job_dicts['train'])
    model.init()
    model.save()

if args.trainer is None:
  train_name = "trainer_" + exp_name
  train_command = "python3 -u train.py" + job_flags['train']

  slurm_script(train_name, train_command, gpu=True, qos='tenenbaum', mem=4096)
else:
  agent_count = 0
  agent_command = "python3 -u run.py" + job_flags['agent']
  for c1 in characters:
    for c2 in characters:
      command = agent_command + " --p1 %s --p2 %s" % (c1, c2)

      #for _ in range(agents):
      agent_name = "agent_%d_%s" % (agent_count, exp_name)
      slurm_script(agent_name, command, log=True, array=agents)
      agent_count += 1
