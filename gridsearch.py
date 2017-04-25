from itertools import product
import os

shared_params = {
  "learning_rate": [0.0001, 0.001, 0.01],
  "reward_halflife": [1,2,3,4],
  "fc_layers": [[128]*1, [128]*2, [128]*3],
  "rnn_layers": [[128]*1, [128]*2, [128]*3],
}


dqn_model = "RecurrentDQN"
dqn_params = {
  "model": ["RecurrentDQN"],
  "temperature": [0.002, 0.02, 0.2],
}
dqn_params.update(shared_params)


rac_model = "RecurrentActorCritic"
rac_params = {
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
  dqn_grid = create_grid(dqn_params)
  for dqn_run in dqn_grid:
    cmd = run_runner(dqn_run)
    print(cmd)
    # os.system(cmd)  # TODO uncomment to run runner.py

if __name__ == "__main__":
  main()
