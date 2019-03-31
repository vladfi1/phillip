import time
from collections import deque

import numpy as np
import gym
import ray
from ray import tune
from ray import rllib
from ray.rllib import agents

from phillip.rllib.test_env import MPEnv, TestEnv

ray.init(
  redis_max_memory=int(4e9),
  object_store_memory=int(4e9),
)

unroll_length = 60
train_batch_size = 128
num_envs = 6
async_env = True
batch_inference = True
fc_depth = 2  # default = 2

base_env = TestEnv

#import psutil
#psutil.Process().cpu_affinity([7])

tune.run_experiments({
  "test": {
    "env": MPEnv if async_env else base_env,
    "run": agents.impala.ImpalaAgent,
    #"run": agents.a3c.A3CAgent,
    #"run": agents.a3c.A2CAgent,
    "checkpoint_freq": 100,
    "config": {
      "env_config": {
        "base_env": base_env,
        
        "num_envs": num_envs if batch_inference else 1,
        "delay": 2,
        #"cpu_affinity": True,
        #"profile": True,

        "step_time_ms": 1,
      },
      "num_gpus": 0.5 if batch_inference else 1,
      "num_cpus_for_driver": 1,
      "optimizer": {
          "train_batch_size": unroll_length * train_batch_size,
          "replay_buffer_num_slots": 4 * train_batch_size + 1,
          "replay_proportion": 0,
          "learner_queue_size": 4,
      },
      #"sample_async": True,
      "sample_batch_size": unroll_length,
      "horizon": 1200,  # one minute
      #"soft_horizon": True,
      "num_workers": 1 if batch_inference else num_envs,
      "num_gpus_per_worker": 0.5 if batch_inference else 0,
      #"num_cpus_per_worker": 2 if async_env else 1,
      "num_envs_per_worker": num_envs if batch_inference else 1,
      # "remote_worker_envs": True,
      "model": {
        #"max_seq_len": unroll_length,
        "use_lstm": True,
        "lstm_use_prev_action_reward": True,
        "fcnet_hiddens": [256] * fc_depth,
      }
    }
  }
})
