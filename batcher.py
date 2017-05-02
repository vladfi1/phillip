import os
import subprocess
import time

SAVE_DIR = "saves/"
LOG_DIR = "slurm_logs/"
TRAIN_TIME = 3600 * 10  # 4 hours

def get_jobs():
  not_ran = set()
  saves = os.listdir(SAVE_DIR)
  logs = [log for log in os.listdir(LOG_DIR) if log.find("trainer")==0 and log.find(".out") > 0]
  for save in saves:
    already_ran = False
    for log in logs:
      if save in log:
        already_ran = True
        break
    if not already_ran:
      not_ran.add(save)
  return not_ran

def get_jobid(job):
  cmd = "squeue -u vladfi1 -o '%i %j %t' | grep {0}".format(job)
  output = subprocess.check_output(cmd, shell=True).strip().split()
  return int(output[0])

def get_status(job_id):
  cmd = "squeue --job {0} -o '%t'".format(job_id)
  output = subprocess.check_output(cmd, shell=True).splitlines()
  if len(output) != 2:
    raise ValueError("Bad output:" + str(output))

  status = output[1]
  if type(status)==bytes:
    status = status.decode("utf-8")
  return status

def get_trainnode(job_id):
  cmd = "squeue --job {0} -o '%N'".format(job_id)
  output = subprocess.check_output(cmd, shell=True).splitlines()
  if len(output) != 2:
    raise ValueError("Bad output:" + str(output))
  node = output[1][4:]
  return int(node)

def main():
  queue = set()
  while True:
    queue.update(get_jobs())

    if len(queue) == 0:
      time.sleep(60)
      continue

    job = queue.pop()

    # start training
    train_cmd  = "python launcher.py {0}/{1} --init".format(SAVE_DIR,job)
    print("Running train command:", train_cmd)
    os.system(train_cmd)

    # make sure the job started
    time.sleep(5)
    job_id = get_jobid(job)
    print("Waiting for job id",str(job_id),"to start.")

    time.sleep(5)
    status = "PD"
    while status == "PD":
      time.sleep(5)
      status = get_status(job_id)

    if status != "R":
      raise ValueError("Bad Status: " + str(status))

    train_machine = get_trainnode(job_id)

    print("Done waiting status =",status,"train machine =",str(train_machine))
    if status is None:
      continue

    agent_cmd = "python launcher.py {0}/{1} --trainer {2}".format(SAVE_DIR, job, train_machine)
    print("Running agent command:",agent_cmd)
    os.system(agent_cmd)

    print("Waiting ",TRAIN_TIME/3600,"hours for training...")
    time.sleep(TRAIN_TIME)

    # stop training
    print("Stopping job",job)
    stop_cmd = "./scancel.sh {0}".format(job)
    os.system(stop_cmd)

    # wait before starting next job
    time.sleep(60)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
  
