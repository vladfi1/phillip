import subprocess
import os

def get_job_node(jobid):
  "Get the reserved node for a job id."
  try:
    output = subprocess.check_output(['squeue', '--job', jobid, '-h', '-o', '%R'])
  except subprocess.CalledProcessError:
    return None # invalid job id
  return int(output[4:-1])

def get_node_ip(node):
  return '172.16.24.%d' % node

def get_job_ip(jobid):
  node = get_job_node(jobid)
  if node is None:
    return None
  return get_node_ip(node)

def get_self_node():
  return os.environ['SLURM_JOB_NODELIST']

def get_self_ip():
  return get_node_ip(get_self_node())