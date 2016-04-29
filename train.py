import RL
import os

# RL.init()
RL.restore()

def sweep(data_dir='experience/'):
  # for f in ["2"]:
  i = 0
  for f in os.listdir(data_dir):
    if f.isdigit():
        filename = data_dir + f
        print("Step", i)
        print("Experience " + filename)
        RL.train(filename)
        i += 1
    else:
        print("Not training on file:", f)
  RL.save()
  #RL.writeGraph()

while True:
  sweep()
