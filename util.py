def scanl(f, init, l):
  r = [init]
  for x in l:
    r.append(f(x, r[-1]))
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

