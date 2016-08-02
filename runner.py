import os
import sys

dry_run = '--dry-run' in sys.argv
#local   = '--local' in sys.argv
#detach  = '--detach' in sys.argv

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
add_param('model', model, both)
#add_param('model', 'ActorCriticSplit', both)
add_param('epsilon', 0.02, both, False)

train_settings = [
  ('optimizer', 'Adam'),
  ('learning_rate', 0.0004),
  ('tdN', 5),
  ('batch_size', 25),
  ('batch_steps', 1),
]

if model.count('DQN'):
  train_settings += [
    ('sarsa', True),
    ('target_delay', 4000),
  ]
  add_param('temperature', 0.002, ['agent'])
elif model.count('ActorCritic'):
  train_settings += [
    ('policy_scale', 0.1),
  ]
  add_param('entropy_scale', 0.001, ['train'], True)

for k, v in train_settings:
  add_param(k, v, ['train'], False)

# agent settings

add_param('dolphin', True, ['agent'], False)

add_param('dump_max', 10, ['agent'], False)

# number of agents playing each matchup
agents = 20
add_param('agents', agents, [])

self_play = False
self_play = 720
add_param('self_play', self_play, ['agent'], False)

add_param('experience_time', 60, ['agent'], False)
add_param('act_every', 3, both)
add_param('delay', 0, ['agent'])
add_param('memory', 0, both)

#movie = 'movies/endless_netplay_battlefield_dual.dtm'
#add_param('movie', movie, ['agent'], False)

characters = [
  'fox',
  'zelda',
  'marth',
#  'roy',
  'falcon',
]

for c in characters:
  exp_name += '_' + c

#add_param('name', exp_name, both, False)
add_param('path', "saves/%s/" % exp_name, both, False)

def slurm_script(name, command, cpus=2, gpu=False, log=False):
  slurmfile = 'slurm_scripts/' + name + '.slurm'
  with open(slurmfile, 'w') as f:
    f.write("#!/bin/bash\n")
    f.write("#SBATCH --job-name=" + name + "\n")
    #if log:
    f.write("#SBATCH --output=slurm_logs/" + name + ".out\n")
    f.write("#SBATCH --error=slurm_logs/" + name + ".err\n")
    f.write("#SBATCH -c%d\n" % cpus)
    f.write("#SBATCH --time=6-23\n")
    #f.write("#SBATCH --cpu_bind=verbose,cores\n")
    #f.write("#SBATCH --cpu_bind=threads\n")
    if gpu:
      f.write("#SBATCH --gres=gpu:titan-x:1\n")
    f.write(command)

  if dry_run:
    print(command)
  else:
    os.system("sbatch " + slurmfile)
    #os.system("sbatch -N 1 -c 2 --mem=8000 --time=6-23:00:00 slurm_scripts/" + jobname + ".slurm &")

init = False
init = True

if dry_run:
  print("NOT starting jobs:")
else:
  print("Starting jobs:")

  # init model for the first time
  if init:
    import RL
    model = RL.Model(mode=RL.Mode.TRAIN, gpu=False, **job_dicts['train'])
    model.init()
    model.save()

train_name = "trainer_" + exp_name
train_command = "python3 -u train.py" + job_flags['train']

slurm_script(train_name, train_command, gpu=True)

#sys.exit()

agent_count = 0
agent_command = "python3 -u run.py" + job_flags['agent']
for c1 in characters:
  for c2 in characters:
    command = agent_command + " --p1 %s --p2 %s" % (c1, c2)

    for _ in range(agents):
      agent_name = "agent_%d_%s" % (agent_count, exp_name)
      slurm_script(agent_name, command)
      agent_count += 1

