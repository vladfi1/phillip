from numpy import random
import functools
import operator
from threading import Thread
import hashlib
import os
import pprint
import time

pp = pprint.PrettyPrinter(indent=2)

def foldl(f, init, l):
  for x in l:
    init = f(init, x)
  return init

def foldl1(f, l):
  return foldl(f, l[0], l[1:])

def foldr(f, init, l):
  for x in reversed(l):
    init = f(x, init)
  return init

def foldr1(f, l):
  return foldr(f, l[-1], l[:-1])

def scanl(f, init, l):
  r = [init]
  for x in l:
    r.append(f(r[-1], x))
  return r

def scanl1(f, l):
  return scanl(f, l[0], l[1:])

def scanr(f, init, l):
  r = [init]
  for x in reversed(l):
    r.append(f(x, r[-1]))
  r.reverse()
  return r

def scanr1(f, l):
  return scanr(f, l[-1], l[:-1])

def zipWith(f, *sequences):
  return [f(*args) for args in zip(*sequences)]

def compose(*fs):
  "compose(f1, f2, ..., fn)(x) = f1(f2( ... fn(x)))"
  def composed(x):
    for f in reversed(fs):
      x = f(x)
    return x
  return composed

def deepMap(f, obj):
  if isinstance(obj, dict):
    return {k : deepMap(f, v) for k, v in obj.items()}
  if isinstance(obj, (list, tuple)):
    return type(obj)(deepMap(f, x) for x in obj)
  return f(obj)

def deepValues(obj):
  if isinstance(obj, dict):
    for v in obj.values():
      for x in deepValues(v):
        yield x
  elif isinstance(obj, list):
    for v in obj:
      for x in deepValues(v):
        yield x
  else: # note that tuples are values, not lists
    yield obj

def deepZip(*objs):
  if len(objs) == 0:
    return []
  
  first = objs[0]
  if isinstance(first, dict):
    return {k : deepZip(*[obj[k] for obj in objs]) for k in first}
  if isinstance(first, (list, tuple)):
    return zipWith(deepZip, *objs)
  return objs

def deepZipWith(f, *objs):
  if len(objs) == 0:
    return []
  
  first = objs[0]
  if isinstance(first, dict):
    return {k : deepZipWith(f, *[obj[k] for obj in objs]) for k in first}
  if isinstance(first, (list, tuple)):
    return type(first)(deepZipWith(f, *vals) for vals in zip(*objs))
  return f(*objs)

def deepItems(obj, path=[]):
  if isinstance(obj, dict):
    for k, v in obj.items():
      yield from deepItems(v, path=path+[k])
  elif isinstance(obj, list):
    for i, v in enumerate(obj):
      yield from deepItems(v, path=path+[i])
  else:
    yield (path, obj)

def deepIter(iters):
  if isinstance(iters, dict):
    deep_iters = [(k, deepIter(v)) for k, v in iters.items()]
    while True:
      try:
        yield {k: v.next() for k, v in deep_iters}
      except StopIteration:
        return
  elif isinstance(iters, (list, tuple)):
    yield from zip(*map(deepIter, iters))
  else:
    yield from iters

def flip(p):
  return random.binomial(1, p)

def product(xs):
  return functools.reduce(operator.mul, xs, 1.0)

def async_map(f, xs):
  n = len(xs)
  ys = n * [None]
  
  def run(i):
    ys[i] = f(xs[i])

  threads = n * [None]
  for i in range(n):
    threads[i] = Thread(target=run, args=[i])
    threads[i].start()
  
  def wait():
    for p in threads:
      p.join()
    return ys
  
  return wait

def chunk(l, n):
  return [l[i:i+n] for i in range(0, len(l), n)]

class MovingAverage:
  def __init__(self, rate=1e-2, initial=0):
    self.rate = rate
    self.avg = initial
  
  def append(self, val):
    self.avg += self.rate * (val - self.avg)

class Timer:
  def reset(self):
    self.time = time.time()
  
  def split(self):
    now = time.time()
    delta = now - self.time
    self.time = now
    return delta

class CircularQueue:
  def __init__(self, size=None, init=None, array=None):
    if array:
      self.size = len(array)
      self.array = array
    else:
      self.size = size
      self.array = [init] * size
    self.index = 0
  
  def push(self, obj):
    self.array[self.index] = obj
    self.increment()
    return self.array[self.index]
  
  def peek(self):
    return self.array[self.index]
  
  def increment(self):
    self.index += 1
    self.index %= self.size
  
  def __getitem__(self, index):
    return self.array[(self.size + self.index + index) % self.size]
  
  def __len__(self):
    return self.size
  
  def as_list(self):
    return self.array[self.index:] + self.array[:self.index]

def hashString(s):
  s = s.encode()
  return hashlib.md5(s).hexdigest()

def port(s):
  print("PORT", s)
  return 5536 + int(hashString(s), 16) % 60000

def makedirs(path):
  if not os.path.exists(path):
    os.makedirs(path)

def update(dikt, **kwargs):
  for k, v in kwargs.items():
    if v is not None:
      dikt[k] = v
    elif k not in dikt:
      dikt[k] = None

def load_params(path, key=None):
  import json
  with open(path + '/params') as f:
    params = json.load(f)
  
  # support old-style separation of params into train and agent
  if key and key in params:
    params.update(params[key])
  
  params.update(path=path)
  return params

