"""
Responsible for interfacing with Dolphin to interface with SSBM, and handles things like:
* character selection
* stage selection
"""

import atexit
import os
import functools
import enum
import time

from phillip import util, ssbm, ctype_util
from phillip.default import *
from . import state_manager, movie, dolphin, reward
from . import memory_watcher as mw
from .state import *
from . import menu_manager as mm
from .pad import Pad

class Player(enum.Enum):
  HUMAN = 1
  AI    = 2
  CPU   = 3

  def is_human(self):
    return self == Player.HUMAN
  
  def needs_pad(self):
    return self != Player.HUMAN

str_to_player = {p.name.lower(): p for p in Player}

class SSBMEnv(Default):
  _options = [
    Option('zmq', type=int, default=1, help="use zmq for memory watcher"),
    Option('tcp', type=int, default=0, help="use zmq over tcp for memory watcher and pipe input"),
    Option('stage', type=str, default="final_destination", choices=movie.stages.keys(), help="which stage to play on"),
    Option('start', type=int, default=1, help="start game in endless time mode"),
    Option('debug', type=int, default=0),
  ] + [
    Option('p%d' % i, type=int, choices=str_to_player.keys(), default='ai',
        help="Player type in port %d.") for i in [1, 2]
  ] + [
    Option('char%d' % i, type=str, choices=mm.characters.keys(), default="falcon",
        help="character for player %d" % i) for i in [1, 2]
  ] + [
    Option('cpu%d' % i, type=int, help="cpu level %d" % i) for i in [1, 2]
  ]
  
  _members = [
    ('dolphin', dolphin.DolphinRunner),
  ]
  
  def __init__(self, **kwargs):
    Default.__init__(self, **kwargs)

    self.toggle = 0

    #self.user = os.path.expanduser(self.user)
    self.user = self.dolphin.user

    # boot to match code is currently hardcoded    
    if self.dolphin.boot_to_match:
      self.cpu2 = 9
    
    # set up players
    self.pids = []
    self.ai_pids = []
    self.players = {}
    self.levels = {}
    self.characters = {}
    for i in range(2):
      j = i + 1
      cpu = getattr(self, 'cpu%d' % j)
      self.levels[i] = cpu
      if cpu:
        player = Player.CPU
      else:
        player = str_to_player[getattr(self, 'p%d' % j)]
      
      self.players[i] = player
      
      if player.needs_pad():
        self.pids.append(i)
        self.characters[i] = getattr(self, 'char%d' % j)

      if player == Player.AI:
        self.ai_pids.append(i)
    
    print(self.players)

    self.state = ssbm.GameMemory()
    self.prev_state = ssbm.GameMemory()
    # track players 1 and 2 (pids 0 and 1)
    self.sm = state_manager.StateManager([0, 1])
    self.write_locations()
    
    print('Creating MemoryWatcher.')
    self.tcp = self.tcp or self.dolphin.windows
    if self.tcp:
      self.mw = mw.MemoryWatcherZMQ(port=5555)
    else:
      mwType = mw.MemoryWatcherZMQ if self.zmq else mw.MemoryWatcher
      self.mw = mwType(path=self.user + '/MemoryWatcher/MemoryWatcher')
    
    pipe_dir = os.path.join(self.user, 'Pipes')
    print('Creating Pads at %s.' % pipe_dir)
    util.makedirs(pipe_dir)
    
    pad_ids = self.pids
    if self.dolphin.netplay:
      pad_ids = [0]
    
    pipe_paths = [os.path.join(pipe_dir, 'phillip%d' % i) for i in pad_ids]
    self.pads = [Pad(path, tcp=self.tcp) for path in pipe_paths]

    self.init_stats()
    
    print('Running dolphin.')
    self.dolphin_process = self.dolphin.run(self.players)
    atexit.register(self.dolphin_process.kill)

    try:
      #time.sleep(2) # wait for dolphin to start up
      connect_pads = util.async_map(lambda pad: pad.connect(), self.pads)
      connect_pads()  # blocks until dolphin is listening
    except KeyboardInterrupt:
      print("Pipes not initialized!")
      return
    
    print("Pipes initialized.")

    # self.navigate_menus()
    
    # get rid of weird initial conditions
    self.update_state()
    for _ in range(10):
      self.mw.advance()
      self.update_state()
    
    self.last_frame = self.state.frame
    self.start_time = time.time()

  def close(self):
    self.dolphin_process.terminate()
    self.print_stats()

  def init_stats(self):
    self.game_frame = 0
    self.total_frames = 1
    self.skip_frames = 0

  def print_stats(self):
    total_time = time.time() - self.start_time
    frac_skipped = self.skip_frames / self.total_frames
    print('Total Time:', total_time)
    print('Total Frames:', self.total_frames)
    print('Average FPS:', self.total_frames / total_time)
    print('Fraction Skipped: {:.6f}'.format(frac_skipped))

  def write_locations(self):
    path = os.path.join(self.dolphin.user, 'MemoryWatcher')
    util.makedirs(path)
    print('Writing locations to:', path)
    with open(os.path.join(path, 'Locations.txt'), 'w') as f:
      f.write('\n'.join(self.sm.locations()))

  def navigate_menus(self):
    pick_chars = []
    
    for pid, pad in zip(self.pids, self.pads):
      pick_chars.append(mm.pick_char(pid, pad, self.characters[pid], self.levels[pid]))
    
    pick_chars = mm.Parallel(*pick_chars)
        
    actions = [pick_chars]
    
    if self.start:
      enter_settings = mm.enter_settings(self.pids[0], self.pads[0])
      
      # sets the game mode and picks the stage
      start_game = movie.Movie(movie.endless_netplay + movie.stages[self.stage], self.pads[0])
      actions += [enter_settings, start_game]
    
    #actions.append(Wait(600))
    
    navigate_menus = mm.Sequential(*actions)
    
    self.update_state()
    char_stages = [menu.value for menu in [Menu.Characters, Menu.Stages]]
  
    print("Navigating menus.")
    while self.state.menu in char_stages:
      self.mw.advance()
      last_frame = self.state.frame
      self.update_state()
      
      if self.state.frame > last_frame:
        navigate_menus.move(self.state)
        
        if navigate_menus.done():
          for pid, pad in zip(self.pids, self.pads):
            if self.characters[pid] == 'sheik':
              pad.press_button(Button.A)
    
    print("setup finished")
    assert(self.state.menu == Menu.Game.value)

  def update_state(self):
    messages = self.mw.get_messages()
    for message in messages:
      self.sm.handle(self.state, *message)
  
  def spam(self, button, period=120):
    self.toggle = (self.toggle + 1) % period
    if self.toggle == 0:
      self.pads[0].press_button(button)
    elif self.toggle == 1:
      self.pads[0].release_button(button)
  
  def step(self, controllers):
    # TODO: if not in game, wait
    
    for pid, pad in zip(self.pids, self.pads):
      if pid not in controllers:
        assert(self.players[pid] == Player.CPU)
        continue
      assert(self.players[pid] == Player.AI)
      if controllers[pid] is not None:
        pad.send_controller(controllers[pid])
    
    ctype_util.copy(self.state, self.prev_state)
    while self.state.frame == self.last_frame:
      self.mw.advance()
      self.update_state()

    skipped_frames = self.last_frame - self.state.frame - 1
    if skipped_frames > 1:
      print("skipped %d frames" % skipped_frames)
      self.skip_frames += skipped_frames
    self.last_frame = self.state.frame
    
    rewards = {}
    for pid in self.ai_pids:
      enemy_pid = 1 - pid
      rewards[pid] = reward.computeRewards(
          [self.prev_state, self.state],
          enemies=[enemy_pid],
          allies=[pid])[0]
    
    return self.state, rewards

  def get_state(self):
    return self.state

