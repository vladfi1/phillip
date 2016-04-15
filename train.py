import RL
import os

RL.restore()

def sweep(data_dir='experience/'):
  for f in os.listdir(data_dir):
    filename = data_dir + f
    print("Training on " + filename)
    RL.train(filename)
  RL.save()
  RL.writeGraph()

while True:
  sweep()
