import time
from collections import deque

import numpy as np
import gym
import ray
from ray import tune
from ray import rllib
from ray.rllib import agents


class TestEnv(rllib.env.MultiAgentEnv):
  def __init__(self, config):
    self._step_time_s = config.get('step_time_ms', 10) / 1000
    self._obs_size = config.get('obs_size', 900)
    self.observation_space = gym.spaces.Box(-1, 1, [self._obs_size], float)
    self._obs = np.zeros([self._obs_size])
    self.action_space = gym.spaces.Discrete(50)

  def _get_obs(self):
    return {0: self._obs}

  def reset(self):
    return self._get_obs()

  def step(self, actions):
    time.sleep(self._step_time_s)
    return self._get_obs(), {0:0}, NONE_DONE, {}


def seq_to_dict(seq):
  return {i: x for i, x in enumerate(seq)}

def map_dict(f, d):
  return {k: f(v) for k, v in d.items()}

NONE_DONE = {"__all__": False}


class AsyncEnv(rllib.env.BaseEnv):
  
  def __init__(self, config):
    print("AsyncEnv", config.keys())
    self._config = config.copy()  # copy necessary for sending config to remotes
    self._base_env_type = config.get("base_env", TestEnv)
    self._remote_env_type = ray.remote(self._base_env_type)
    self._dummy_env = self._base_env_type(config)
    self.action_space = self._dummy_env.action_space
    self.observation_space = self._dummy_env.observation_space
    self._first_poll = True

    self._num_envs = config["num_envs"]
    self._delay = config["delay"]
    self._queue = deque()
  
  def first_poll(self):
    self._envs = []

    for i in range(self._num_envs):
      config = self._config.copy()
      if self._config.get("cpu_affinity"):
        psutil.Process().cpu_affinity([6])
        config["cpu"] = i
      self._envs.append(self._remote_env_type.remote(config))

    obs = ray.get([env.reset.remote() for env in self._envs])
    rewards = [map_dict(lambda _: 0., ob) for ob in obs]
    dones = [NONE_DONE for ob in obs]
    infos = [map_dict(lambda _: {}, ob) for ob in obs]
    
    dummy_actions = [map_dict(lambda _: 0, ob) for ob in obs]
    for _ in range(self._delay):
      self.send_actions(dummy_actions)
    
    self._first_poll = False
    return tuple(map(seq_to_dict, (obs, rewards, dones, infos))) + ({},)
    
  def poll(self):
    if self._first_poll:
      return self.first_poll()
    fetched = ray.get(self._queue.popleft())
    return tuple(map(seq_to_dict, zip(*fetched))) + ({},)

  def send_actions(self, action_dict):
    if len(action_dict) == 0:
      import ipdb; ipdb.set_trace()
    self._queue.append([
        env.step.remote(action_dict[i])
        for i, env in enumerate(self._envs)
    ])

  def try_reset(self, env_id):
    return ray.get(self._envs[env_id].reset.remote())


ray.init(
  redis_max_memory=int(4e9),
  object_store_memory=int(4e9),
)

unroll_length = 60
train_batch_size = 128
num_envs = 1
async_env = False
batch_inference = False

batch_inference = async_env and batch_inference
base_env = TestEnv

#import psutil
#psutil.Process().cpu_affinity([7])

tune.run_experiments({
  "test": {
    "env": AsyncEnv if async_env else base_env,
    "run": agents.impala.ImpalaAgent,
    #"run": agents.a3c.A3CAgent,
    #"run": agents.a3c.A2CAgent,
    "checkpoint_freq": 100,
    "config": {
      "env_config": {
        "base_env": base_env,
        
        "num_envs": num_envs if batch_inference else 1,
        "delay": 0,
        #"cpu_affinity": True,
        #"profile": True,

        "step_time_ms": 1,
      },
      "num_gpus": 0.5 if batch_inference else 1,
      "num_cpus_for_driver": 1,
      "optimizer": {
          "train_batch_size": unroll_length * train_batch_size,
          "replay_buffer_num_slots": 4 * train_batch_size + 1,
          "replay_proportion": 3.,
          "learner_queue_size": 1,
      },
      "sample_async": True,
      "sample_batch_size": unroll_length,
      "horizon": 1200,  # one minute
      #"soft_horizon": True,
      "num_workers": 1 if batch_inference else num_envs,
      "num_gpus_per_worker": 0.5 if batch_inference else 0,
      #"num_cpus_per_worker": 2 if async_env else 1,
      # "num_envs_per_worker": 2,
      # "remote_worker_envs": True,
      "model": {
        #"max_seq_len": unroll_length,
        "use_lstm": True,
        "lstm_use_prev_action_reward": True,
      }
    }
  }
})
