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

def zipWith(f, l1, l2):
  return [f(a1, a2) for a1, a2 in zip(l1, l2)]

