"""Contains plain rllib code (no ssbm)."""

import time
import numpy as np
import gym
from ray import rllib
import numpy as np

def seq_to_dict(seq):
  return {i: x for i, x in enumerate(seq)}

def map_dict(f, d):
  return {k: f(v) for k, v in d.items()}

NONE_DONE = {"__all__": False}

class TestEnv(rllib.env.MultiAgentEnv):
  """Test environment that just sleeps during step."""

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

import atexit

# inspired by openai baselines subproc_vec_env
def run_env(conn, env_fn, config):
  env = env_fn(config)
  atexit.register(env.close)

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


class MPEnv(rllib.env.MultiAgentEnv):
  """A single env running in a seprate process.

  Has a fixed delay to buffer actions and observations.
  Use with num_envs_per_worker > 1.
  """
  
  def __init__(self, config):
    print("MPEnv", config.keys())
    self._config = config.copy()
    self._base_env_type = config.get("base_env", TestEnv)
    self._dummy_env = self._base_env_type(self._config)
    self.action_space = self._dummy_env.action_space
    self.observation_space = self._dummy_env.observation_space
    self._delay = config["delay"]
    self._first_reset = True

  def reset(self):
    if self._first_reset:
      ctx = mp.get_context(self._config.get("mp_context", "spawn"))
      self._conn, child_conn = ctx.Pipe()
      env_fn = CloudpickleWrapper(self._base_env_type)
      self._env_process = ctx.Process(target=run_env, args=(child_conn, env_fn, self._config))
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
    data = self._conn.recv()
    self._last_obs = data[0]
    return data

  def close(self):
    self._conn.send(('close', None))
    #self._env_process.terminate


class BaseMPEnv(rllib.env.BaseEnv):
  """Vectorized MultiAgent env that uses multiprocessing."""
  
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
    self._num_envs = config.get("num_envs", 1)
    self._first_poll = True

  def batch_recv(self):
    return [conn.recv() for conn in self._conns]

  def batch_send(self, cmd, args=None):
    for conn in self._conns:
      conn.send((cmd, args))
  
  def first_poll(self):
    ctx = mp.get_context(self._config.get("mp_context", "spawn"))
    self._conns, child_conns = zip(*[
        ctx.Pipe() for _ in range(self._num_envs)])
    self._env_procs = []
    for i, conn in enumerate(child_conns):
      config = self._config.copy()
      if self._config.get("cpu_affinity"):
        config["cpu"] = i
      proc = ctx.Process(
          target=run_env,
          args=(conn, self._env_fn, config))
      proc.daemon = True
      proc.start()
      self._env_procs.append(proc)

    self.batch_send('reset')
    obs = self.batch_recv()
    self._last_obs = obs

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
    data = self.batch_recv()
    data = tuple(map(seq_to_dict, zip(*data))) + ({},)
    self._last_obs = data[0]
    return data

  def send_actions(self, actions):
    for env_id, conn in enumerate(self._conns):
      conn.send(('step', actions[env_id]))

  def try_reset(self, env_id):
    return self._last_obs[env_id]

  def close(self):
    self.batch_send('close')
    #self._env_process.terminate()


class AsyncEnv(rllib.env.BaseEnv):
  """Uses actors for the remotes, which is currently too slow."""
  
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
    #self._queues = [deque() for _ in range(self._num_envs)]
    #self._timeout = config.get("timeout")

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
    assert(len(self._queue) == self._delay)

  def try_reset(self, env_id):
    return ray.get(self._envs[env_id].reset.remote())

