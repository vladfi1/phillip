import os
import sys

dry_run = '--dry-run' in sys.argv
local   = '--local' in sys.argv
detach  = '--detach' in sys.argv

if not os.path.exists("slurm_logs"):
    os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
    os.makedirs("slurm_scripts")

exp_name = "exp"
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

add_param('model', 'ActorCritic', both)
add_param('epsilon', 0.02, both)

train_settings = [
  ('learning_rate', 0.001),
  ('tdN', 5),
  ('batch_size', 10),
  ('batch_steps', 1),
  #('sarsa', True'),
  #('target_delay', 5000),
  ('entropy_scale', 0.007),
]

for k, v in train_settings:
  add_param(k, v, ['train'])

# agent settings

add_param('dolphin', True, ['agent'], False)

add_param('dump_max', 20, ['agent'])

agents = 25
add_param('agents', agents, [])

self_play = False
add_param('self_play', self_play, ['agent'])

movie = 'FalconFalcon' if self_play else 'Falcon9Falcon'

dual = True
add_param('dual', dual, [])
if dual:
  movie += '_dual'
movie += '.dtm'

add_param('movie', movie, ['agent'], False)

#add_param('name', exp_name, both, False)
add_param('path', "saves/%s/" % exp_name, both, False)

def slurm_script(name, command, cpus=2, gpu=False):
  slurmfile = 'slurm_scripts/' + name + '.slurm'
  with open(slurmfile, 'w') as f:
    f.write("#!/bin/bash\n")
    f.write("#SBATCH --job-name=" + name + "\n")
    f.write("#SBATCH --output=slurm_logs/" + name + ".out\n")
    f.write("#SBATCH --error=slurm_logs/" + name + ".err\n")
    f.write("#SBATCH -c%d\n" % cpus)
    if gpu:
      f.write("#SBATCH --gres=gpu:1\n")
    f.write(command)

  if dry_run:
    print(command)
  else:
    os.system("sbatch " + slurmfile)
    #os.system("sbatch -N 1 -c 2 --mem=8000 --time=6-23:00:00 slurm_scripts/" + jobname + ".slurm &")

init = False
#init = True

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

#slurm_script(train_name, train_command, gpu=True)

#sys.exit()

agent_command = "python3 -u run.py" + job_flags['agent']
for i in range(agents):
  agent_name = "agent_%d_%s" % (i, exp_name)
  cpus = 4 if dual else 2
  slurm_script(agent_name, agent_command, cpus)

