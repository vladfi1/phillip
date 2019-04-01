import os
import enum
import subprocess

import phillip
from phillip import util
from phillip.default import *

datapath = phillip.path + '/data'

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

with open(datapath + '/Dolphin.ini', 'r') as f:
  dolphin_ini = f.read()

gfx_ini = """
[Settings]
Crop = True
DumpFormat = {dump_format}
DumpCodec = {dump_codec}
DumpEncoder = {dump_encoder}
DumpPath = {dump_path}
"""

gale01_ini = """
[Gecko_Enabled]
"""

default_ini = """
$Netplay Community Settings
"""

exi_ini = """
$DMA Read Before Poll
"""

speedhack_ini = """
$Speed Hack
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

boot_to_match_ini = """
$Fox vs Fox-9
$Boot To Match
$Skip Memcard Prompt
"""

class DolphinRunner(Default):
  _options = [
    Option('exe', type=str, default='dolphin-emu-nogui', help="dolphin executable"),
    Option('user', type=str, help="path to dolphin user directory"),
    Option('iso', type=str, default="SSBM.iso", help="path to SSBM iso"),
    Option('movie', type=str, help="path to dolphin movie file to play at startup"),
    Option('setup', type=int, default=1, help="setup custom dolphin directory"),
    Option('gui', action="store_true", default=False, help="run with graphics and sound at normal speed"),
    Option('mute', action="store_true", default=False, help="mute game audio"),
    Option('windows', action='store_true', help="set defaults for windows"),
    Option('netplay', type=str, help="join traversal server"),

    Option('port1', type=int, help='device in port 1'),
    Option('port2', type=int, help='device in port 2'),

    Option('gfx', type=str, default="Null", help="graphics backend"),
    Option('dual_core', type=int, default=1, help="Use separate gpu and cpu threads."),
    Option('audio', type=str, default="No audio backend", help="audio backend"),
    Option('speed', type=int, default=0, help='framerate - 1=normal, 0=unlimited'),
    Option('dump_frames', action="store_true", default=False, help="dump frames from dolphin to disk"),
    Option('pipe_count', type=int, default=0, help="Count pipes alphabetically. Turn on for older dolphins."),
    Option('direct', action="store_true", default=False, help="netplay direct connect"),
    Option('fullscreen', action="store_true", default=False, help="run dolphin with fullscreen"),
    Option('iso_path', type=str, default="", help="directory where you keep your isos"),
    Option('fm', action="store_true", help="set up config for Faster Melee"),
    Option('dump_format', type=str, default='mp4'),
    Option('dump_codec', type=str, default='h264'),
    Option('dump_encoder', type=str, default=''),
    Option('dump_path', type=str, default=''),
    Option('lcancel_flash', action="store_true", help="flash on lcancel"),
    Option('boot_to_match', action="store_true", help="boot to match with gecko codes"),
    Option('exi', type=int, default=1, help="use if memory watcher is inside EXI device"),
    Option('speedhack', action="store_true", help="run game at unlimited speed"),
  ]

  def setup_user(self, players):
    configDir = os.path.join(self.user, 'Config')
    util.makedirs(configDir)

    ai_pids = []
    for pid, player in players.items():
      port_attr = 'port%d' % (pid+1)
      si_device = 0
      if player.needs_pad():
        ai_pids.append(pid)
        si_device = 6
      elif player.is_human():
        si_device = 12
      setattr(self, port_attr, si_device)

    with open(configDir + '/GCPadNew.ini', 'w') as f:
      f.write(generateGCPadNew([0] if self.netplay else ai_pids, self.pipe_count))

    with open(configDir + '/Dolphin.ini', 'w') as f:
      config_args = dict(
        user=self.user,
        gfx=self.gfx,
        cpu_thread=bool(self.dual_core),
        dump_frames=self.dump_frames,
        audio=self.audio,
        speed=self.speed,
        netplay=self.netplay,
        traversal='direct' if self.direct else 'traversal',
        fullscreen=self.fullscreen,
        iso_path=self.iso_path,
        port1=self.port1,
        port2=self.port2,
      )
      f.write(dolphin_ini.format(**config_args))
    
    with open(configDir + '/GFX.ini', 'w') as f:
      f.write(gfx_ini.format(
        dump_path=self.dump_path,
        dump_codec=self.dump_codec,
        dump_encoder=self.dump_encoder,
        dump_format=self.dump_format))

    gameSettings = self.user + '/GameSettings'
    util.makedirs(gameSettings)
    with open(gameSettings + '/GALE01.ini', 'w') as f:
      if self.fm:
        ini = gale01_ini_fm
      else:
        ini = gale01_ini
        if self.exi:
          ini += exi_ini
        if self.speedhack:
          ini += speedhack_ini
        if self.boot_to_match:
          ini += boot_to_match_ini
        else:
          ini += default_ini
        if self.lcancel_flash:
          ini += lcancel_ini
      print(ini)
      f.write(ini)

    util.makedirs(self.user + '/Dump/Frames')
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)
        
    if self.user is None:
      import tempfile
      self.user = tempfile.mkdtemp() + '/'
    
    print("Dolphin user dir", self.user)

    # with exi, the frame counter is changed and doesn't work in menus
    # so we have to boot straight into the match
    if self.speedhack or self.exi:
      self.boot_to_match = True
    
    if self.gui or self.windows:
      self.speedhack = 0
      # switch from headless to gui
      if self.exe.endswith("-headless"):
        #self.exe = self.exe[:-9]
        self.exe = self.exe[:-9] + "-nogui"
      
      # Note: newer dolphins use 'DX11', but win-mw is an old fork.
      self.gfx = 'D3D' if self.windows else 'OGL'
      self.speed = 1
      
      if self.mute:
        self.audio = 'No audio backend'
      else:
        self.audio = 'XAudio2' if self.windows else 'Pulse'
  
  def run(self, players):
    if self.setup:
      self.setup_user(players)

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
  DolphinRunner.update_parser(parser)
  args = parser.parse_args()
  
  runner = DolphinRunner(**args.__dict__)
  runner.run({})


if __name__ == "__main__":
  main()
