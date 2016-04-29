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

def compose(f, g):
  "compose(f, g)(x) = f(g(x))"
  return lambda x: f(g(x))

def deepMap(f, obj):
  if isinstance(obj, dict):
    return {k : deepMap(f, v) for k, v in obj.items()}
  if isinstance(obj, list):
    return [deepMap(f, x) for x in obj]
  return f(obj)

