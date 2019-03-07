import argparse
import ray
from ray import tune
from ray.rllib import agents

from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib import ray_env

parser = argparse.ArgumentParser()
SSBMEnv.update_parser(parser)
args = parser.parse_args()


ray.init()

tune.run_experiments({
  "test": {
    "env": ray_env.AsyncSSBMEnv,
    #"run": agents.impala.ImpalaAgent,
    #"run": agents.a3c.A3CAgent,
    "run": agents.a3c.A2CAgent,
    "config": {
      "env_config": {
        "ssbm_config": args.__dict__,  # config to pass to env class
        "episode_length": None,
        "num_envs": 1,
        "delay": 1,
      },
      "horizon": 1200,  # one minute
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

