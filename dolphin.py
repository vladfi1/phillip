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
"""
#Triggers/L-Analog = `Axis L -+`
#Triggers/R-Analog = `Axis R -+`

def generatePipeConfig(player, count):
  config = "[GCPad%d]\n" % (player+1)
  config += "Device = Pipe/%d/phillip%d\n" % (count, player)
  config += pipeConfig
  return config

# TODO: make this configurable
def generateGCPadNew(pids=[1]):
  config = ""
  count = 0
  for p in sorted(pids):
    config += generatePipeConfig(p, count)
    count += 1
  return config

with open('Dolphin.ini', 'r') as f:
  dolphinConfig = f.read()

import shutil
import os
import util
from default import *

class SetupUser(Default):
  _options = [
    Option('gfx', type=str, default="Null", help="graphics backend"),
    Option('cpu_thread', action="store_true", default=False, help="Use separate gpu and cpu threads."),
    Option('cpus', type=int, nargs='+', default=[1], help="Which players are cpu-controlled."),
    Option('audio', type=str, default="No audio backend", help="audio backend"),
    Option('speed', type=int, default=0, help='framerate - 100=normal, 0=unlimited'),
    Option('dump_frames', action="store_true", default=False, help="dump frames from dolphin to disk"),
  ]
  
  def __call__(self, user):
    configDir = user + 'Config/'
    util.makedirs(configDir)

    with open(configDir + 'GCPadNew.ini', 'w') as f:
      f.write(generateGCPadNew(self.cpus))

    with open(configDir + 'Dolphin.ini', 'w') as f:
      config_args = dict(
        user=user,
        gfx=self.gfx,
        cpu_thread=self.cpu_thread,
        dump_frames=self.dump_frames,
        audio=self.audio,
        speed=self.speed
      )
      f.write(dolphinConfig.format(**config_args))

    # don't need memory card with netplay
    #gcDir = user + 'GC/'
    #os.makedirs(gcDir, exist_ok=True)
    #memcardName = 'MemoryCardA.USA.raw'
    #shutil.copyfile(memcardName, gcDir + memcardName)
    
    gameSettings = "GameSettings/"
    shutil.copytree(gameSettings, user + gameSettings)

    util.makedirs(user + 'Dump/Frames/')

import subprocess

class DolphinRunner(Default):
  _options = [
    Option('exe', type=str, default='dolphin-emu-headless', help="dolphin executable"),
    Option('user', type=str, help="path to dolphin user directory"),
    Option('iso', type=str, default="SSBM.iso", help="path to SSBM iso"),
    Option('movie', type=str, help="path to dolphin movie file to play at startup"),
    Option('setup', type=int, default=1, help="setup custom dolphin directory"),
    Option('gui', action="store_true", default=False, help="run with graphics and sound at normal speed"),
    Option('mute', action="store_true", default=False, help="mute game audio"),
  ]
  
  _members = [
    ('setupUser', SetupUser)
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, init_members=False, **kwargs)
    
    if self.user is None:
      self.user = 'dolphin-test/'
  
    if self.gui:
      self.exe = 'dolphin-emu-nogui'
      kwargs.update(
        speed = 1,
        gfx = 'OGL',
      )
      
      if self.mute:
        kwargs.update(audio = 'No audio backend')
      else:
        kwargs.update(audio = 'ALSA')
      
    if self.setup:
      self._init_members(**kwargs)
      self.setupUser(self.user)
  
  def __call__(self):
    args = [self.exe, "--user", self.user, "--exec", self.iso]
    if self.movie is not None:
      args += ["--movie", self.movie]
    
    return subprocess.Popen(args)

