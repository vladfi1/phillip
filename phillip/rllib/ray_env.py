import gym
import ray

from phillip import ssbm
from phillip.env.ssbm_env import SSBMEnv
from phillip.rllib import ssbm_spaces


class MultiSSBMEnv(ray.rllib.env.MultiAgentEnv):

  def __init__(self, config):
    self._config = config
    self._env = None
    self._act_every = config.get("act_every", 3)
    action_set = ssbm.actionTypes["custom_sh2_wd"]
    self._action_chains = action_set.get_action_chains(self._act_every)
    
    #self.action_space = None
    self.action_space = gym.spaces.Discrete(action_set.size)
    #self.action_space = {
    #  pid: ssbm_spaces.controller_space
    #  for pid in self._env.ai_pids
    #}
    #self.observation_space = None
    self.observation_space = ssbm_spaces.game_conv_list[0].space
    #self.observation_space = {
    #    pid: ssbm_spaces.game_conv_list[pid].space
    #    for pid in self._env.ai_pids
    #}
  
  def _get_obs(self):
    game_state = self._env.get_state()
    return {
      pid: ssbm_spaces.game_conv_list[pid](game_state)
      for pid in self._env.ai_pids
    }

  def reset(self):
    if self._env is None:
      self._env = SSBMEnv(**self._config)
    return self._get_obs()
  
  def step(self, actions):
    chains = {pid: self._action_chains[action] for pid, action in actions.items()}
    
    for i in range(self._act_every):
      self._env.step({
          pid: chain[i].get_real_controller(self._env.characters[pid])
          for pid, chain in chains.items()
       })
    
    obs = self._get_obs()
    rewards = {i: 0 for i in range(2)}
    dones = {i: False for i in range(2)}
    dones.update(__all__=False)
    return obs, rewards, dones, {}

