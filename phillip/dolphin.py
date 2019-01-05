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

def generateGCPadNew(pids=[1], pipe_count=True):
  config = ""
  count = 0
  for p in sorted(pids):
    config += generatePipeConfig(p, count if pipe_count else 0)
    count += 1
  return config

import phillip
datapath = phillip.path + '/data'

with open(datapath + '/Dolphin.ini', 'r') as f:
  dolphin_ini = f.read()

gfx_ini = """
[Settings]
DumpFramesAsImages = {dump_ppm}
DumpFramesToPPM = {dump_ppm}
DumpFramesCounter = False
Crop = True
DumpFormat = {dump_format}
DumpCodec = {dump_codec}
DumpEncoder = {dump_encoder}
DumpPath = {dump_path}
"""

gale01_ini = """
[Gecko_Enabled]
$Netplay Community Settings
"""

lcancel_ini = """
$Flash White on Successful L-Cancel
"""
#$Flash Red on Unsuccessful L-Cancel


gale01_ini_fm = """
[Core]
CPUThread = True
GPUDeterminismMode = fake-completion
PollingMethod = OnSIRead
[Gecko_Enabled]
$Faster Melee Netplay Settings
$Lag Reduction
$Game Music ON
"""

import os
from phillip import util
from phillip.default import *

class SetupUser(Default):
  _options = [
    Option('gfx', type=str, default="Null", help="graphics backend"),
    Option('dual_core', type=int, default=1, help="Use separate gpu and cpu threads."),
    Option('cpus', type=int, nargs='+', default=[1], help="Which players are cpu-controlled."),
    Option('audio', type=str, default="No audio backend", help="audio backend"),
    Option('speed', type=int, default=0, help='framerate - 1=normal, 0=unlimited'),
    Option('dump_frames', action="store_true", default=False, help="dump frames from dolphin to disk"),
    Option('dump_ppm', action="store_true", help="dump frames as ppm images"),
    Option('pipe_count', type=int, default=0, help="Count pipes alphabetically. Turn on for older dolphins."),
    Option('netplay', type=str),
    Option('direct', action="store_true", default=False, help="netplay direct connect"),
    Option('fullscreen', action="store_true", default=False, help="run dolphin with fullscreen"),
    Option('iso_path', type=str, default="", help="directory where you keep your isos"),
    Option('human', action="store_true", help="set p1 to human"),
    Option('fm', action="store_true", help="set up config for Faster Melee"),
    Option('dump_format', type=str, default='mp4'),
    Option('dump_codec', type=str, default='h264'),
    Option('dump_encoder', type=str, default=''),
    Option('dump_path', type=str, default=''),
    Option('lcancel_flash', action="store_true", help="flash on lcancel"),
  ]
  
  def __call__(self, user):
    configDir = user + '/Config'
    util.makedirs(configDir)
    
    if self.dump_ppm:
      self.dump_frames = True

    with open(configDir + '/GCPadNew.ini', 'w') as f:
      f.write(generateGCPadNew([0] if self.netplay else self.cpus, self.pipe_count))

    with open(configDir + '/Dolphin.ini', 'w') as f:
      config_args = dict(
        user=user,
        gfx=self.gfx,
        cpu_thread=bool(self.dual_core),
        dump_frames=self.dump_frames,
        audio=self.audio,
        speed=self.speed,
        netplay=self.netplay,
        traversal='direct' if self.direct else 'traversal',
        fullscreen=self.fullscreen,
        iso_path=self.iso_path,
        port1 = 12 if self.human else 6,
      )
      f.write(dolphin_ini.format(**config_args))
    
    with open(configDir + '/GFX.ini', 'w') as f:
      f.write(gfx_ini.format(
        dump_ppm=self.dump_ppm,
        dump_path=self.dump_path,
        dump_codec=self.dump_codec,
        dump_encoder=self.dump_encoder,
        dump_format=self.dump_format))

    gameSettings = user + '/GameSettings'
    util.makedirs(gameSettings)
    with open(gameSettings + '/GALE01.ini', 'w') as f:
      ini = gale01_ini_fm if self.fm else gale01_ini
      if self.lcancel_flash:
        ini += lcancel_ini
      f.write(ini)

    util.makedirs(user + '/Dump/Frames')

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
    Option('windows', action='store_true', help="set defaults for windows"),
    Option('netplay', type=str, help="join traversal server"),
  ]
  
  _members = [
    ('setupUser', SetupUser)
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, init_members=False, **kwargs)
    
    if self.user is None:
      import tempfile
      self.user = tempfile.mkdtemp() + '/'
    
    print("Dolphin user dir", self.user)
    
    #if self.netplay: # need gui version to netplay
    #  index = self.exe.rfind('dolphin-emu') + len('dolphin-emu')
    #  self.exe = self.exe[:index]
    
    if self.gui or self.windows:
      # switch from headless to gui
      if self.exe.endswith("-headless"):
        #self.exe = self.exe[:-9]
        self.exe = self.exe[:-9] + "-nogui"
      
      # Note: newer dolphins use 'DX11', but win-mw is an old fork.
      kwargs.update(
        speed = 1,
        gfx = 'D3D' if self.windows else 'OGL',
      )
      
      if self.mute:
        kwargs.update(audio = 'No audio backend')
      else:
        kwargs.update(audio = 'XAudio2' if self.windows else 'Pulse')
      
    if self.setup:
      self._init_members(**kwargs)
      self.setupUser(self.user)
  
  def __call__(self):
    args = [self.exe, "--user", self.user]
    if not self.netplay:
      args += ["--exec", self.iso]
    if self.movie is not None:
      args += ["--movie", self.movie]
    
    print(args)
    process = subprocess.Popen(args)
    
    if self.netplay:
      import time
      time.sleep(2) # let dolphin window spawn
      
      import pyautogui
      #import ipdb; ipdb.set_trace()
      pyautogui.click(150, 150)
      #pyautogui.click(50, 50)
      time.sleep(0.5)
      pyautogui.hotkey('alt', 't') # tools

      time.sleep(0.5)
      pyautogui.hotkey('n') # netplay
      
      time.sleep(1) # allow netplay window time to spawn
      
      #return process
      
      #pyautogui.hotkey('down') # traversal
      
      #for _ in range(3): # move to textbox
      #  pyautogui.hotkey('tab')
      
      #pyautogui.typewrite(self.netplay) # write traversal code
      
      #return process
      
      time.sleep(0.1)
      # connect
      #pyautogui.hotkey('tab')
      pyautogui.hotkey('enter')

      #import ipdb; ipdb.set_trace()
    
    return process

def main():
  import argparse
  
  parser = argparse.ArgumentParser()
  
  for opt in DolphinRunner.full_opts():
    opt.update_parser(parser)
  
  args = parser.parse_args()
  
  runner = DolphinRunner(**args.__dict__)
  runner()


if __name__ == "__main__":
  main()
