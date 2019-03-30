from collections import deque
import os
import psutil
import cProfile
import time

import numpy as np
import gym
import ray
from ray import rllib

from phillip import ssbm
from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib import ssbm_spaces


class MultiSSBMEnv(rllib.env.MultiAgentEnv):

  def __init__(self, config):
    print("MultiSSBMEnv", config.keys())
    self._ssbm_config = config["ssbm_config"]
    self._flat_obs = config.get("flat_obs", False)
    self._episode_length = config["episode_length"]
    self._steps_this_episode = 0
    self._cpu = config.get('cpu')
    self._profile = config.get('profile', False)
    self._env = None
    self._act_every = config.get("act_every", 3)
    action_set = ssbm.actionTypes["custom_sh2_wd"]
    self._action_chains = action_set.get_action_chains(self._act_every)
    
    #self.action_space = None
    self.action_space = gym.spaces.Discrete(action_set.size)
    #self.observation_space = None
    if self._flat_obs:
      self.observation_space = gym.spaces.Box(
        low=-10, high=10,
        shape=(ssbm_spaces.game_conv_list[0].flat_size,),
        dtype=np.float32)
    else:
      self.observation_space = ssbm_spaces.game_conv_list[0].space
    print(self.observation_space)

  def _get_obs(self):
    game_state = self._env.get_state()
    return {
        pid: self._convs[pid](game_state)
        for pid in self._env.ai_pids
    }

  def reset(self):
    if self._env is None:
      self._env = SSBMEnv(**self._ssbm_config)
      if self._cpu is not None:
        psutil.Process().cpu_affinity([self._cpu])
        # set cpu affinity on dolphin process and all threads
        os.system('taskset -a -c -p %d %d' % (self._cpu, self._env.dolphin_process.pid))

      if self._profile:
        self._profile_counter = 0
        self._profiler = cProfile.Profile()
        #self._profiler.enable()

      self._convs = {
          pid: ssbm_spaces.game_conv_list[pid]
          for pid in self._env.ai_pids
      }
      if self._flat_obs:
        self._convs = {pid: conv.make_flat for pid, conv in self._convs.items()}

    return self._get_obs()

  def step(self, actions):
    if self._profile:
      self._profile_counter += 1
      if self._profile_counter % 10000 == 0:
        self._profiler.dump_stats('/tmp/ssbm_stats')
      return self._profiler.runcall(self._step, actions)
    return self._step(actions)

  def _step(self, actions):
    self._steps_this_episode += 1
    chains = {pid: self._action_chains[action] for pid, action in actions.items()}
    
    rewards = {i: 0 for i in self._env.ai_pids}
    for i in range(self._act_every):
      _, step_rewards = self._env.step({
          pid: chain[i].get_real_controller(self._env.characters[pid])
          for pid, chain in chains.items()
      })
      for pid, r in step_rewards.items():
        rewards[pid] += r
    
    obs = self._get_obs()

    done = self._steps_this_episode == self._episode_length
    if done:
      print("episode terminated")
      self._steps_this_episode = 0
    #dones = {i: done for i in self._env.ai_pids}
    #dones.update(__all__=done)
    dones = {"__all__": done}
    return obs, rewards, dones, {}


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
    self._base_env_type = config.get("base_env", MultiSSBMEnv)
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

