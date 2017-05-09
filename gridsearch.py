from itertools import product
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="RecurrentDQN", help="RecurrentDQN or RecurrentActorCritic")
parser.add_argument("--num_samples", type=int, default=50, help="Instead of using the whole grid, sample randomly")
parser.add_argument("--dry_run", action="store_true", help="Don't actually run runner.py, just print out the cmds")
args = parser.parse_args()


# Choose the parameters you want to grid search over
shared_params = {
  "learning_rate": [0.0001, 0.001, 0.01],
  "reward_halflife": [1,2,3,4],
  "fc_layers": [[128]*1, [128]*2, [128]*3],
  "rnn_layers": [[128]*1, [128]*2, [128]*3],
}


# These parameters are unique to DQN
dqn_params = {
  "model": ["RecurrentDQN"],
  "temperature": [0.002, 0.02, 0.2],
}
dqn_params.update(shared_params)


# These parameters are unique to ActorCritic
rac_params = {
  "model": ["RecurrentActorCritic"],
  "entropy_scale": [0.001, 0.01, 0.1],
}
rac_params.update(shared_params)

def create_grid(params):
  """Returns a list of dicts containing the set-product of 
  the keys in params.
  e.g.
  In [0]: a = {"a": [1,2], "b": [10,20]}
  In [1]: create_grid(a)
  Out[1]: [{'a': 1, 'b': 10}, {'a': 2, 'b': 10}, {'a': 1, 'b': 20}, {'a': 2, 'b': 20}]
  """
  paramlist = []
  for k,v in params.items():
    params = []
    for p in v:
      params.append((k,p))
    paramlist.append(params)
  return [dict(i) for i in product(*paramlist)]

def run_runner(params):
  cmd = "python runner.py "
  for k,v in params.items():
    cmd += " --" + k
    if type(v) == list:
      v = " ".join([str(i) for i in v])
    else:
      v = str(v)
    cmd += " " + v
  return cmd

def main():
  """Loop through the parameter dictionaries and run the command.
  """
  if args.model.find("DQN"):
    params = dqn_params
  else:
    params = rac_params

  grid = create_grid(params)
  if args.num_samples > len(grid):
    args.num_samples = len(grid)
  sample_idx = np.random.choice(range(len(grid)), size=args.num_samples, replace=False)
  for i, run in enumerate(grid):
    if i not in sample_idx: continue
    cmd = run_runner(run)
    cmd += " --prefix batch"

    if args.dry_run:
      print(cmd)
    else:
      os.system(cmd)

if __name__ == "__main__":
  main()
