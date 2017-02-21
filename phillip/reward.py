import numpy as np
from . import util

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
def computeRewards(state_actions, enemies=[0], allies=[1], damage_ratio=0.01):
  players = enemies + allies

  deaths = {p : processDeaths([isDying(sa.state.players[p]) for sa in state_actions]) for p in players}
  damages = {p : processDamages([sa.state.players[p].percent for sa in state_actions]) for p in players}

  losses = {p : deaths[p] + damage_ratio * damages[p] for p in players}

  return sum(losses[p] for p in enemies) - sum(losses[p] for p in allies)

# TODO: unfinished
def computeRewards_vectorized(states, enemies=[0], allies=[1], damage_ratio=0.01):
  players = enemies + allies

  deaths = {p : processDeaths(list(map(isDyingAction, states['players'][p]['action_state']))) for p in players}
  damages = {p : processDamages([s.players[p].percent for s in states]) for p in players}

  losses = {p : deaths[p] + damage_ratio * damages[p] for p in players}

  return sum(losses[p] for p in enemies) - sum(losses[p] for p in allies)

