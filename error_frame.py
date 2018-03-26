import numpy as np
import pickle

error_frame_path = 'agents/delay12/FalcoBF/0/error_frame'

with open(error_frame_path, 'rb') as f:
  error_frame = pickle.load(f)

state = error_frame['state']
del state['frame']

def check_io(checker):
  def wrapper(f):
    def g(*args, **kwargs):
      output = f(*args, **kwargs)
      checker(output, *args, **kwargs)
      return output
    return g
  return wrapper

def check(output, struct):
  assert isinstance(output[0], list)
  assert follow(output[0], struct) == output[1]

def follow(path, struct):
  for key in path:
    struct = struct[key]
  return struct  

@check_io(check)
def reduce_max(struct):
  if isinstance(struct, (tuple, list)):
    maxes = list(map(reduce_max, struct))
    best_index = 0
    best_max = maxes[0]
    
    for i in range(1, len(maxes)):
      if maxes[i][1] > best_max[1]:
        best_index = i
        best_max = maxes[i]
    
    return [best_index] + best_max[0], best_max[1]
  elif isinstance(struct, dict):
    keys, values = zip(*struct.items())
    path, value = reduce_max(values)
    return [keys[path[0]]] + path[1:], value
    
  elif isinstance(struct, np.ndarray):
    index = np.argmax(struct)
    return [index], struct[index]
  
  assert TypeError('invalid struct')

error_path, error_value = reduce_max(state)
print(error_path, error_value)

