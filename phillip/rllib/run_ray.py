import argparse
import ray
from ray.rllib.agents import impala

from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib.ray_env import MultiSSBMEnv

parser = argparse.ArgumentParser()
SSBMEnv.update_parser(parser)
args = parser.parse_args()


ray.init()
trainer = impala.ImpalaAgent(env=MultiSSBMEnv, config={
    "env_config": args.__dict__,  # config to pass to env class
    "num_workers": 1,
    "num_envs_per_worker": 1,
    #"remote_worker_envs": True,
})

while True:
  print(trainer.train())

