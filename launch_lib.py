import subprocess

def add_options(parser):
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
  parser.add_argument('--cpu', action='store_true', help="don't run trainer on a gpu")
  parser.add_argument('--gpu', type=str, default='GEFORCEGTX1080TI', help='gpu type')
  parser.add_argument('--send', type=int, default=1, help='send params with zmq PUB/SUB')
  parser.add_argument('--pop_size', type=int, help='max pop size')
  parser.add_argument('--fast_cpu', action="store_true", help='run agents faster on haswell cpus')


def launch(
  args, name, command, cpus=2, mem=1, gpu=False, log=True, qos=None,
  array=None, depends=None, pids=[]):

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
      opt("-x node069,node067,node060")
      f.write("source ~/.cuda\n")
      f.write("source activate tf-gpu-src\n")
    else:
      if args.fast_cpu:
        f.write("source activate tf-cpu-src\n")
        opt("-x node[001-030]")
      else:
        f.write("source activate tf-cpu-opt\n")
      f.write("sleep 40s\n")
    f.write(command)

  #command = "screen -S %s -dm srun --job-name %s --pty singularity exec -B $OM_USER/phillip -B $HOME/phillip/ -H ../home phillip.img gdb -ex r --args %s" % (name[:10], name, command)
  output = subprocess.check_output(["sbatch", slurmfile]).decode()
  print(output)
  jobid = output.split()[-1].strip()
  return jobid
