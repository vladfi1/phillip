import numpy as np
from . import util
from .default import *
import enum
import tensorflow as tf

def isDying(player):
  # see https://docs.google.com/spreadsheets/d/1JX2w-r2fuvWuNgGb6D3Cs4wHQKLFegZe2jhbBuIhCG8/edit#gid=13
  return player.action_state <= 0xA

# players tend to be dead for many frames in a row
# here we prune all but the first frame of the death
def processDeaths(deaths):
  return np.array(util.zipWith(lambda prev, next: float((not prev) and next), deaths, deaths[1:]))

def processDamages(percents):
  return np.array(util.zipWith(lambda prev, next: max(next-prev, 0), percents, percents[1:]))

# from player 2's perspective
def computeRewards(states, enemies=[0], allies=[1], damage_ratio=0.01):
  pids = enemies + allies

  deaths = {p : processDeaths([isDying(s.players[p]) for s in states]) for p in pids}
  damages = {p : processDamages([s.players[p].percent for s in states]) for p in pids}

  losses = {p : deaths[p] + damage_ratio * damages[p] for p in pids}

  return sum(losses[p] for p in enemies) - sum(losses[p] for p in allies)

# from StateActions instead of just States
def computeRewardsSA(state_actions, **kwargs):
  states = [sa.state for sa in state_actions]
  return computeRewards(states, **kwargs)

def compute_deaths(player, lib=np):
  dead = player['action_state'] <= 0xA
  deaths = lib.logical_and(lib.logical_not(dead[:-1]), dead[1:])
  if lib == tf: deaths = tf.to_float(deaths)
  return deaths

def compute_damages(player, lib=np):
  percents = player['percent']
  damages = lib.maximum(percents[1:] - percents[:-1], 0)
  if lib == tf: damages = tf.to_float(damages)
  return damages

def compute_rewards(states, enemies=[0], allies=[1], damage_ratio=0.01, lib=np):
  """Computes rewards from a list of state transitions.
  
  Args:
    states: A structure of numpy arrays of length T, as given by ctype_util.vectorizeCTypes.
    enemies: The list of pids on the enemy team.
    allies: The list of pids on our team.
    damage_ratio: How much damage (percent) counts relative to stocks.
  Returns:
    A length T numpy array with the rewards on each transition.
  """
  
  players = states['players']
  pids = enemies + allies

  deaths = {p : compute_deaths(players[p], lib) for p in pids}
  damages = {p : compute_damages(players[p], lib) for p in pids}
  losses = {p : deaths[p] + damage_ratio * damages[p] for p in pids}
  
  return sum(losses[p] for p in enemies) - sum(losses[p] for p in allies)


def distance(state, lib=np):
  players = state['players']
  x0 = players[0]['x']
  y0 = players[0]['y']
  x1 = players[1]['x']
  y1 = players[1]['y']
  
  dx = x1 - x0
  dy = y1 - y0
  
  return -lib.sqrt(lib.square(dx) + lib.square(dy))


def pseudo_rewards(states, potential_fn, gamma, lib=np):
  potentials = potential_fn(states, lib=lib)
  return potentials, gamma * potentials[1:] - potentials[:-1]
