pipeConfig = """
Buttons/A = `Button A`
Buttons/B = `Button B`
Buttons/X = `Button X`
Buttons/Y = `Button Y`
Buttons/Z = `Button Z`
Main Stick/Up = `Axis MAIN Y +`
Main Stick/Down = `Axis MAIN Y -`
Main Stick/Left = `Axis MAIN X -`
Main Stick/Right = `Axis MAIN X +`
Triggers/L = `Button L`
Triggers/R = `Button R`
D-Pad/Up = `Button D_UP`
D-Pad/Down = `Button D_DOWN`
D-Pad/Left = `Button D_LEFT`
D-Pad/Right = `Button D_RIGHT`
Buttons/Start = `Button START`
C-Stick/Up = `Axis C Y +`
C-Stick/Down = `Axis C Y -`
C-Stick/Left = `Axis C X -`
C-Stick/Right = `Axis C X +`
Triggers/L-Analog = `Axis L -+`
Triggers/R-Analog = `Axis R -+`
"""

def generatePipeConfig(player, count):
  config = "[GCPad%d]\n" % (player+1)
  config += "Device = Pipe/%d/phillip%d\n" % (count, player)
  config += pipeConfig
  return config

# TODO: make this configurable
def generateGCPadNew(cpus=[1]):
  config = ""
  count = 0
  for p in cpus:
    config += generatePipeConfig(p, count)
    count += 1
  return config

with open('Dolphin.ini', 'r') as f:
  dolphinConfig = f.read()

import shutil
import os

def setupUser(user='dolphin-test/'):
  configDir = user + 'Config/'
  os.makedirs(configDir, exist_ok=True)

  with open(configDir + 'GCPadNew.ini', 'w') as f:
    f.write(generateGCPadNew())

  with open(configDir + 'Dolphin.ini', 'w') as f:
    f.write(dolphinConfig.format(user=user))

  gcDir = user + 'GC/'
  os.makedirs(gcDir, exist_ok=True)
  memcardName = 'MemoryCardA.USA.raw'
  shutil.copyfile(memcardName, gcDir + memcardName)

import subprocess

def runDolphin(exe='dolphin-emu-nogui', user='dolphin-test/', movie="Fox5FalconBattlefield.dtm", iso="SSBM.iso", setup=True):
  if setup:
    setupUser(user)
  args = [exe, "--user", user, "--exec", iso]
  if movie is not None:
    args += ["--movie", movie]
  return subprocess.Popen(args)

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser()

  parser.add_argument("--prefix", default="parallel/")
  parser.add_argument("--count", type=int, default=1)

  args = parser.parse_args()

  processes = [runDolphin(user=args.prefix + "%d/" % i) for i in range(args.count)]
