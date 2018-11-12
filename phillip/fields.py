import typing
import attr
import tensorflow as tf
import numpy as np

def getField(obj, field):
  if isinstance(field, str):
    return getattr(obj, field)
  else:
    return obj[field]

def setField(obj, field, val, validate=True):
  if isinstance(field, str):
    if validate:
      if not hasattr(obj, field):
        raise TypeError("%s object has no field %s" % (type(obj), field))
    setattr(obj, field, val)
  else: # assume an array
    obj[field] = val

def getPath(obj, path):
  for field in path:
    obj = getField(obj, field)
  return obj

# doesn't work with empty path :(
def setPath(obj, path, val):
  obj = getPath(obj, path[:-1])
  setField(obj, path[-1], val)


def tupleFactory(*fs):
  return attr.Factory(lambda: tuple(f() for f in fs))

# TODO: figure out how to propagate defaults
def makeTupleType(t):
  return typing.NamedTuple(t.__name__, [(a.name, a.type) for a in t.__attrs_attrs__])

py2tf = {
  bool : tf.bool,
  float : tf.float32,
  int : tf.int32,
}

def type_placeholders(t, shape=None, name=""):
  if t in py2tf:
    return tf.placeholder(py2tf[t], shape, name)
  if isinstance(t, typing.TupleMeta):
    return tuple(type_placeholders(s, shape, name + "/" + str(i)) for i, s in enumerate(t.__args__))
  # assume a "record" type with __annotations__
  return {f : type_placeholders(s, shape, name + "/" + f) for f, s in t.__annotations__.items()}


def make_buffer(t, size, default=0):
  if t in py2tf:
    if default is attr.NOTHING: default = 0
    return np.fill([size], default, dtype=t)
  elif isinstance(t, typing.TupleMeta):
    return tuple(make_buffer(s, size) for s in t.__args__)
  return {a.name: make_buffer(a.type, size, a.default) for a in t.__attrs_attrs__}

def set_buffer(index, buf, val):
  if isinstance(buf, np.array):
    assert(isinstance(val, buf.dtype))
    buf[index] = val
  elif isinstance(buf, tuple):
    assert(isinstance(val, tuple))
    assert(len(buf) == len(val))
    for b, v in zip(buf, val):
      set_buffer(index, b, v)
  elif isinstance(buf, dict):
    for k, b in buf.items():
      set_buffer(index, b, getattr(val, k))

def vectorize_type(t, values):
  if t in py2tf:
    return np.array(values)
  elif isinstance(t, typing.TupleMeta):
    return [vectorize_type(s, [v[i] for v in values]) for i, s in enumerate(t.__args__)]
  return {f : vectorize_type(s, [getattr(v, f) for v in values]) for f, s in t.__annotations__.items()}

