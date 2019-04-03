import argparse
import ray
from ray import tune
from ray.rllib import agents

from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib import ssbm_env, rllib_env

parser = argparse.ArgumentParser()
SSBMEnv.update_parser(parser)
parser.add_argument('--num_workers', type=int)
parser.add_argument('--num_envs_per_worker', type=int)
parser.add_argument('--cluster', action='store_true')
args = parser.parse_args()


if args.cluster:
  ray.init(
    redis_address="10.0.1.45:6379"
  )
else:
  ray.init(
    redis_max_memory=int(4e9),
    object_store_memory=int(4e9),
  )

unroll_length = 60
train_batch_size = 128
num_workers = args.num_workers or 2
num_envs = args.num_envs_per_worker or 2
async_env = True
batch_inference = True
vec_env = False  # batch using a single vectorized env
fc_depth = 2
fc_width = 256
use_test_env = False

#if not use_test_env:
#  args.

batch_inference = async_env and batch_inference
vec_env = vec_env and batch_inference
base_env = rllib_env.TestEnv if use_test_env else ssbm_env.MultiSSBMEnv
exp_name = "test" if use_test_env else "ssbm"
#import psutil
#psutil.Process().cpu_affinity([7])

top_env = base_env
if async_env:
  top_env = rllib_env.BaseMPEnv if vec_env else rllib_env.MPEnv

tune.run_experiments({
  exp_name: {
    "env": top_env,
    "run": agents.impala.ImpalaAgent,
    #"run": agents.a3c.A3CAgent,
    #"run": agents.a3c.A2CAgent,
    "checkpoint_freq": 100,
    "config": {
      "env_config": {
        "base_env": base_env,
        
        "ssbm_config": args.__dict__,  # config to pass to env class
        "episode_length": None,
        "num_envs": num_envs if vec_env else 1,
        "delay": 2,
        "flat_obs": True,
        #"cpu_affinity": True,
        #"profile": True,

        "step_time_ms": 1,
      },
      "num_gpus": 0.4 if batch_inference else 1,
      "num_cpus_for_driver": 1,
      "optimizer": {
          "train_batch_size": unroll_length * train_batch_size,
          "replay_buffer_num_slots": 4 * train_batch_size + 1,
          "replay_proportion": 0,
          "learner_queue_size": 16,
      },
      #"sample_async": True,
      "sample_batch_size": unroll_length,
      "horizon": 1200,  # one minute
      #"soft_horizon": True,
      "num_workers": num_workers if batch_inference else num_envs,
      "num_gpus_per_worker": 0.1 if batch_inference else 0,
      "num_cpus_per_worker": (1+num_envs) if batch_inference else 1,
      "num_envs_per_worker": 1 if vec_env else num_envs,
      # "remote_worker_envs": True,
      "model": {
        #"max_seq_len": unroll_length,
        "use_lstm": True,
        "lstm_use_prev_action_reward": True,
        "fcnet_hiddens": [fc_width] * fc_depth,
      }
    }
  }
})
