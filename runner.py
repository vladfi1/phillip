import os
import sys

dry_run = '--dry-run' in sys.argv
local   = '--local' in sys.argv
detach  = '--detach' in sys.argv
agents = '--agents' in sys.argv

if not os.path.exists("slurm_logs"):
    os.makedirs("slurm_logs")

if not os.path.exists("slurm_scripts"):
    os.makedirs("slurm_scripts")


train_params = {
  'init': True,
}

model = 'ActorCritic'
#model = 'DQN'
name = model
train_params['model'] = model

movie = 'Falcon9Falcon'
#name += '_' + movie

learning_rate = 1e-4
train_params['learning_rate'] = learning_rate
name += '_' + str(learning_rate)

tdN = 5
train_params['tdN'] = tdN
name += '_' + str(tdN)

batch_size = 10
train_params['batch_size'] = batch_size
name += '_' + str(batch_size)

if model.endswith('DQN'):
  sarsa = False
  #sarsa = True
  train_params['sarsa'] = sarsa
  if sarsa:
    name += '_sarsa'

  target_delay = None
  target_delay = 5000
  train_params['target_delay'] = target_delay
  if target_delay:
    name += '_' + str(target_delay)
elif model == 'ActorCritic':
  entropy_scale = 0.005
  train_params['entropy_scale'] = entropy_scale
  name += '_' + str(entropy_scale)

train_params['name'] = name

trainer_jobs = [train_params]
if agents:
  trainer_jobs=[]

agent_jobs = []

n_agents = 50
if not agents:
  n_agents = 0
for _ in range(n_agents):
    exemplar = {
            'model': model,
            'movie': movie + '.dtm',
            'dump_max': 10,
            'dolphin': True,
            'self_play': False,
            'name': name,
        }
    agent_jobs.append(exemplar)


if dry_run:
    print("NOT starting jobs:")
else:
    print("Starting jobs:")

for i, job in enumerate(trainer_jobs):
    jobname = "trainer_" + str(i)
    flagstring = ""
    for flag in job:
        if isinstance(job[flag], bool):
            if job[flag]:
                jobname = jobname + "_" + flag
                flagstring = flagstring + " --" + flag
            else:
                print("WARNING: Excluding 'False' flag " + flag)
        # elif flag == 'import':
        #     imported_network_name = job[flag]
        #     if imported_network_name in base_networks.keys():
        #         network_location = base_networks[imported_network_name]
        #         jobname = jobname + "_" + flag + "_" + str(imported_network_name)
        #         flagstring = flagstring + " --" + flag + " " + str(network_location)
        #     else:
        #         jobname = jobname + "_" + flag + "_" + str(job[flag])
        #         flagstring = flagstring + " --" + flag + " " + networks_prefix + "/" + str(job[flag])
        else:
            jobname = jobname + "_" + flag + "_" + str(job[flag])
            flagstring = flagstring + " --" + flag + " " + str(job[flag])
    # flagstring = flagstring + " --name " + jobname

    jobcommand = "python3 -u train.py" + flagstring

    print(jobcommand)
    if local and not dry_run:
        if detach:
            os.system(jobcommand + ' 2> slurm_logs/' + jobname + '.err 1> slurm_logs/' + jobname + '.out &')
        else:
            os.system(jobcommand)

    else:
        with open('slurm_scripts/' + jobname + '.slurm', 'w') as slurmfile:
            slurmfile.write("#!/bin/bash\n")
            slurmfile.write("#SBATCH --job-name"+"=" + jobname + "\n")
            slurmfile.write("#SBATCH --output=slurm_logs/" + jobname + ".out\n")
            slurmfile.write("#SBATCH --error=slurm_logs/" + jobname + ".err\n")
            slurmfile.write(jobcommand)

        if not dry_run:
            # if 'gpu' in job and job['gpu']:
            os.system("sbatch --gres=gpu:1 slurm_scripts/" + jobname + ".slurm")
            # else:
            #     os.system("sbatch -N 1 -c 2 --mem=8000 --time=6-23:00:00 slurm_scripts/" + jobname + ".slurm &")

for i, job in enumerate(agent_jobs):
    jobname = "agent_" + str(i)
    flagstring = ""
    for flag in job:
        if isinstance(job[flag], bool):
            if job[flag]:
                jobname = jobname + "_" + flag
                flagstring = flagstring + " --" + flag
            else:
                print("WARNING: Excluding 'False' flag " + flag)
        # elif flag == 'import':
        #     imported_network_name = job[flag]
        #     if imported_network_name in base_networks.keys():
        #         network_location = base_networks[imported_network_name]
        #         jobname = jobname + "_" + flag + "_" + str(imported_network_name)
        #         flagstring = flagstring + " --" + flag + " " + str(network_location)
        #     else:
        #         jobname = jobname + "_" + flag + "_" + str(job[flag])
        #         flagstring = flagstring + " --" + flag + " " + networks_prefix + "/" + str(job[flag])
        else:
            jobname = jobname + "_" + flag + "_" + str(job[flag])
            flagstring = flagstring + " --" + flag + " " + str(job[flag])
    # flagstring = flagstring + " --name " + jobname

    jobcommand = "python3 -u run.py" + flagstring

    print(jobcommand)
    if local and not dry_run:
        if detach:
            os.system(jobcommand + ' 2> slurm_logs/' + jobname + '.err 1> slurm_logs/' + jobname + '.out &')
        else:
            os.system(jobcommand)

    else:
        with open('slurm_scripts/' + jobname + '.slurm', 'w') as slurmfile:
            slurmfile.write("#!/bin/bash\n")
            slurmfile.write("#SBATCH --job-name"+"=" + jobname + "\n")
            slurmfile.write("#SBATCH --output=slurm_logs/" + jobname + ".out\n")
            slurmfile.write("#SBATCH --error=slurm_logs/" + jobname + ".err\n")
            slurmfile.write(jobcommand)

        if not dry_run:
            # if 'gpu' in job and job['gpu']:
            #     os.system("sbatch -c 2 --gres=gpu:titan-x:1 --mem=8000 --time=6-23:00:00 slurm_scripts/" + jobname + ".slurm &")
            # else:
            os.system("sbatch slurm_scripts/" + jobname + ".slurm &")
