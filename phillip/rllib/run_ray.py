import argparse
import ray
from ray import tune
from ray.rllib.agents import impala

from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib.ray_env import MultiSSBMEnv

parser = argparse.ArgumentParser()
SSBMEnv.update_parser(parser)
args = parser.parse_args()


ray.init()

tune.run_experiments({
  "impala": {
    "env": MultiSSBMEnv,
    "run": impala.ImpalaAgent,
    "config": {
      "env_config": args.__dict__,  # config to pass to env class
      "num_workers": 1,
      # "num_envs_per_worker": 2,
      # "remote_worker_envs": True,
      "model": {
        "use_lstm": True,
        "lstm_use_prev_action_reward": True,
      }
    }
  }
})

