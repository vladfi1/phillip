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
#Triggers/L-Analog = `Axis L -+`
#Triggers/R-Analog = `Axis R -+`
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

def setupUser(user,
  gfx="Null",
  cpu_thread=False,
  cpus=[1],
  dump_frames=False,
  audio="No audio backend",
  speed=0,
  **unused):
  configDir = user + 'Config/'
  os.makedirs(configDir, exist_ok=True)

  with open(configDir + 'GCPadNew.ini', 'w') as f:
    f.write(generateGCPadNew(cpus))

  with open(configDir + 'Dolphin.ini', 'w') as f:
    config_args = dict(
      user=user,
      gfx=gfx,
      cpu_thread=cpu_thread,
      dump_frames=dump_frames,
      audio=audio,
      speed=speed
    )
    print("dump_frames", dump_frames)
    f.write(dolphinConfig.format(**config_args))

  gcDir = user + 'GC/'
  os.makedirs(gcDir, exist_ok=True)
  memcardName = 'MemoryCardA.USA.raw'
  shutil.copyfile(memcardName, gcDir + memcardName)

import subprocess

def runDolphin(
  exe='dolphin-emu-nogui',
  user='dolphin-test/',
  iso="SSBM.iso",
  movie=None,
  setup=True,
  self_play=False,
  gui=False,
  mute=False,
  **kwargs):
  
  if gui:
    exe = 'dolphin-emu-nogui'
    kwargs.update(
      speed = 1,
      gfx = 'OGL',
    )
    
    if mute:
      kwargs.update(audio = 'No audio backend')
    else:
      kwargs.update(audio = 'ALSA')
  
  cpus = [0, 1] if self_play else [1]
  
  if setup:
    setupUser(user, cpus=cpus, **kwargs)
  args = [exe, "--user", user, "--exec", iso]
  if movie is not None:
    args += ["--movie", movie]
  
  return subprocess.Popen(args)

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser()

  parser.add_argument("--iso", default="SSBM.iso", help="path to game iso")
  parser.add_argument("--prefix", default="parallel/")
  parser.add_argument("--count", type=int, default=1)
  parser.add_argument("--movie", type=str)
  parser.add_argument("--gfx", type=str, default="Null", help="graphics backend")
  parser.add_argument("--cpu_thread", action="store_true", help="dual core")
  parser.add_argument("--self_play", action="store_true", help="cpu trains against itself")
  parser.add_argument("--exe", type=str, default="dolphin-emu-nogui", help="dolphin executable")

  args = parser.parse_args()

  processes = [runDolphin(user=args.prefix + "%d/" % i, **args.__dict__) for i in range(args.count)]

  try:
    for p in processes:
      p.wait()
  except KeyboardInterrupt:
    for p in processes:
      p.terminate()
