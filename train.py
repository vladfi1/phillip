import RL
import os

RL.init()
# RL.restore()

def sweep(data_dir='experience/'):
  # for f in ["2"]:
  for f in os.listdir(data_dir):
    if f.isdigit():
        filename = data_dir + f
        print("Training on " + filename)
        RL.train(filename)
    else:
        print("Not training on file:", f)
  RL.save()
  RL.writeGraph()

while True:
  sweep()
