import numpy as np
from phillip import util

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

def deaths_np(player):
  deaths = player['action_state'] <= 0xA
  return np.logical_and(np.logical_not(deaths[:-1]), deaths[1:])

def damages_np(player):
  percents = player['percent']
  return np.maximum(percents[1:] - percents[:-1], 0)

def rewards_np(states, enemies=[0], allies=[1], damage_ratio=0.01):
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

  deaths = {p : deaths_np(players[p]) for p in pids}
  damages = {p : damages_np(players[p]) for p in pids}
  losses = {p : deaths[p] + damage_ratio * damages[p] for p in pids}
  
  return sum(losses[p] for p in enemies) - sum(losses[p] for p in allies)

