import argparse

from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib import ssbm_env, rllib_env

parser = argparse.ArgumentParser()
SSBMEnv.update_parser(parser)
#parser.add_argument('--num_workers', type=int)
parser.add_argument('--num_envs', type=int, default=1)
parser.add_argument('--cpu_affinity', action="store_true")
args = parser.parse_args()

base_env = ssbm_env.MultiSSBMEnv

config = {
    "base_env": base_env,
    
    "ssbm_config": args.__dict__,
    "episode_length": None,
    "num_envs": args.num_envs,
    "delay": 2,
    "flat_obs": True,
    "cpu_affinity": args.cpu_affinity,
    "mp_context": "fork",
    #"profile": True,

    "step_time_ms": 1,
}

vec_env = rllib_env.BaseMPEnv(config)
obs = vec_env.poll()[0]

dummy_actions = {i: {0: 0} for i in range(args.num_envs)}


class EMA:
  def __init__(self, lr=1e-2, init=0.):
    self._lr = 1e-2
    self._init = init
    self._x = init
  
  def update(self, x):
    self._x += self._lr * (x - self._x)
  
  @property
  def value(self):
    return self._x


import time

if __name__ == "__main__":
  start_time = time.time()
  steps = 0
  try:
    while True:
      vec_env.send_actions(dummy_actions)
      vec_env.poll()
      
      steps += 1
      
      if steps % 5000 == 0:
        elapsed_time = time.time() - start_time
        env_steps = steps * args.num_envs
        fps = env_steps / elapsed_time
        print(int(elapsed_time), env_steps, int(fps))
  except KeyboardInterrupt:
    vec_env.close()
