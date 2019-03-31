import time
import numpy as np
import gym
from ray import rllib
import numpy as np

def map_dict(f, d):
  return {k: f(v) for k, v in d.items()}

NONE_DONE = {"__all__": False}

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

  def close(self):
    pass

# inspired by openai baselines subproc_vec_env
def run_env(conn, env_fn, config):
  env = env_fn(config)

  try:
    while True:
      cmd, args = conn.recv()
      if cmd == 'step':
        conn.send(env.step(args))
      elif cmd == 'reset':
        conn.send(env.reset())
      elif cmd == 'close':
        conn.close()
        break
  finally:
    env.close()


class CloudpickleWrapper(object):
    """
    Uses cloudpickle to serialize contents (otherwise multiprocessing tries to use pickle)
    """

    def __init__(self, x):
        self.x = x

    def __getstate__(self):
        import cloudpickle
        return cloudpickle.dumps(self.x)
        
    def __setstate__(self, ob):
        import pickle
        self.x = pickle.loads(ob)

    def __call__(self, *args, **kwargs):
        return self.x(*args, **kwargs)

import multiprocessing as mp
ctx = mp.get_context('spawn')  # apparently this is better

class MPEnv(rllib.env.MultiAgentEnv):
  
  def __init__(self, config):
    print("MPEnv", config.keys())
    self._config = config.copy()
    self._base_env_type = config.get("base_env", TestEnv)
    self._env_fn = CloudpickleWrapper(self._base_env_type)
    #self._base_env_type = TestEnv
    self._dummy_env = self._base_env_type(self._config)
    self.action_space = self._dummy_env.action_space
    self.observation_space = self._dummy_env.observation_space
    self._delay = config["delay"]
    self._first_reset = True

  def reset(self):
    if self._first_reset:
      self._conn, child_conn = ctx.Pipe()
      self._env_process = ctx.Process(target=run_env, args=(child_conn, self._env_fn, self._config))
      self._env_process.daemon = True
      self._env_process.start()
      self._first_reset = False
    else:
      #return self._last_obs
      # clear out delayed obs
      #print("clearing out delayed obs")
      for _ in range(self._delay):
        self._conn.recv()

    self._conn.send(('reset', None))
    self._last_obs = self._conn.recv()

    # send initial delayed action
    dummy_actions = map_dict(lambda _: 0, self._last_obs)
    for _ in range(self._delay):
      self._conn.send(('step', dummy_actions))
    
    return self._last_obs

  def step(self, actions):
    self._conn.send(('step', actions))
    return self._conn.recv()

  def close(self):
    self._conn.send(('close', None))
    #self._env_process.terminate()
