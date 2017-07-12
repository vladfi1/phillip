#!/usr/bin/env python3

import numpy as np
import glob
from phillip import util
import pickle

use_hickle = True
if use_hickle:
  import hickle

path = "experience/FalconFalconBF"

def load_experience(path):
  with open(path, 'rb') as f:
    return pickle.load(f)

def prune_experience(experience):
  state = experience['state']
  state['players'] = state['players'][:2]
  return experience

prune_load = util.compose(prune_experience, load_experience)

paths = glob.glob(path+'/*')[:100]
experiences = []
for i, p in enumerate(paths):
  if i % 10 == 0:
    print('reading %d/%d' % (i, len(paths)))
  experiences.append(prune_load(p))

def to_array(*xs):
  return np.array(xs)

merged = util.deepZipWith(to_array, *experiences)
# hickle can't handle empty lists :(
# but we don't want the initial state anyways
del merged['initial']

if use_hickle:
  hickle.dump(merged, 'merged.hickle')
else:
  with open('merged.pickle', 'wb') as f:
    pickle.dump(merged, f)

