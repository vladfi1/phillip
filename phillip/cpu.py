"""
Responsible for interfacing with Dolphin to interface with SSBM, and handles things like:
* character selection
* stage selection
* running Phillip within SSBM

Should probably be renamed from CPU.py
"""


from . import ssbm, state_manager, agent, util, movie
from . import memory_watcher as mw
from .state import *
from .menu_manager import *
import os
from .pad import *
import time
from . import ctype_util as ct
from numpy import random
from .default import *
import functools

class CPU(Default):
    _options = [
      Option('tag', type=int),
      Option('user', type=str, help="dolphin user directory"),
      Option('zmq', type=int, default=0, help="use zmq for memory watcher"),
      Option('stage', type=str, default="final_destination", choices=movie.stages.keys(), help="which stage to play on"),
      Option('enemy', type=str, help="load enemy agent from file"),
      Option('enemy_reload', type=int, default=0, help="enemy reload interval"),
      Option('enemy_id', type=int, default=-1, help="enemy population id"),
      Option('cpu', type=int, help="enemy cpu level"),
      Option('start', type=int, default=1, help="start game in endless time mode"),
      Option('netplay', type=str),
      Option('frame_limit', type=int, help="stop after a given number of frames"),
      Option('debug', type=int, default=0),
      Option('tcp', type=int, default=0, help="use zmq over tcp for memory watcher and pipe input"),
      Option('windows', action='store_true', help="set defaults for windows"),
      Option('enemy_dump', type=int, default=0, help="also dump frames for the enemy"),
    ] + [Option('p%d' % i, type=str, choices=characters.keys(), default="falcon", help="character for player %d" % i) for i in [1, 2]]
    
    _members = [
      ('agent', agent.Agent),
    ]
    
    def __init__(self, **kwargs):
        Default.__init__(self, **kwargs)

        self.toggle = 0

        self.user = os.path.expanduser(self.user)               

        self.state = ssbm.GameMemory()
        # track players 1 and 2 (pids 0 and 1)
        self.sm = state_manager.StateManager([0, 1])
        self.write_locations()

        if self.tag is not None:
            random.seed(self.tag)
        
        pids = [1, 0]
        if self.agent.swap: pids.reverse()
        self.pid, enemy_pid = pids
        
        self.pids = [self.pid]
        self.agents = {self.pid: self.agent}
        self.cpus = {self.pid: None}
        self.characters = {self.pid: self.agent.char or self.p2}

        if self.enemy:
            enemy_kwargs = util.load_params(self.enemy, 'agent')
            enemy_kwargs.update(
                reload=self.enemy_reload,
                swap=not self.agent.swap,
                dump=self.enemy_dump,
                pop_id=self.enemy_id,
                gpu=self.agent.actor.gpu,
            )
            enemy = agent.Agent(**enemy_kwargs)
        
            self.pids.append(enemy_pid)
            self.agents[enemy_pid] = enemy
            self.cpus[enemy_pid] = None
            self.characters[enemy_pid] = enemy.char or self.p1
        elif self.cpu:
            self.pids.append(enemy_pid)
            self.agents[enemy_pid] = None
            self.cpus[enemy_pid] = self.cpu
            self.characters[enemy_pid] = self.p1

        
        print('Creating MemoryWatcher.')
        self.tcp = self.tcp or self.windows
        if self.tcp:
          self.mw = mw.MemoryWatcherZMQ(port=5555)
        else:
          mwType = mw.MemoryWatcherZMQ if self.zmq else mw.MemoryWatcher
          self.mw = mwType(path=self.user + '/MemoryWatcher/MemoryWatcher')
        
        pipe_dir = self.user + '/Pipes/'
        print('Creating Pads at %s. Open dolphin now.' % pipe_dir)
        util.makedirs(self.user + '/Pipes/')
        
        pads = self.pids
        if self.netplay:
          pads = [0]
        
        paths = [pipe_dir + 'phillip%d' % i for i in pads]
        
        makePad = functools.partial(Pad, tcp=self.tcp)
        self.get_pads = util.async_map(makePad, paths)

        self.init_stats()

    def run(self, frames=None, dolphin_process=None):
        try:
            self.pads = self.get_pads()
        except KeyboardInterrupt:
            print("Pipes not initialized!")
            return
        
        print("Pipes initialized.")
        
        pick_chars = []
        
        tapA = [
            (0, movie.pushButton(Button.A)),
            (0, movie.releaseButton(Button.A)),
        ]
        
        for pid, pad in zip(self.pids, self.pads):
            actions = []
            
            cpu = self.cpus[pid]
            locator = locateCSSCursor(pid)
            
            if cpu:
                actions.append(MoveTo([0, 20], locator, pad, True))
                actions.append(movie.Movie(tapA, pad))
                actions.append(movie.Movie(tapA, pad))
                actions.append(MoveTo([0, -14], locator, pad, True))
                actions.append(movie.Movie(tapA, pad))
                actions.append(MoveTo([cpu * 1.1, 0], locator, pad, True))
                actions.append(movie.Movie(tapA, pad))
                #actions.append(Wait(10000))
            
            actions.append(MoveTo(characters[self.characters[pid]], locator, pad))
            actions.append(movie.Movie(tapA, pad))
            
            pick_chars.append(Sequential(*actions))
        
        pick_chars = Parallel(*pick_chars)
        
        enter_settings = Sequential(
            MoveTo(settings, locateCSSCursor(self.pids[0]), self.pads[0]),
            movie.Movie(tapA, self.pads[0])
        )
        
        # sets the game mode and picks the stage
        start_game = movie.Movie(movie.endless_netplay + movie.stages[self.stage], self.pads[0])
        
        actions = [pick_chars]
        
        if self.start:
            actions += [enter_settings, start_game]
        
        #actions.append(Wait(600))
        
        self.navigate_menus = Sequential(*actions)
        
        print('Starting run loop.')
        self.start_time = time.time()
        
        try:
            while self.game_frame != self.frame_limit:
              self.advance_frame()
        except KeyboardInterrupt:
            if dolphin_process is not None:
                dolphin_process.terminate()
                #hack to get C-zmq dolphin to shutdown properly
                #self.update_state()
                #self.mw.advance()
            self.print_stats()
        
        if dolphin_process is not None:
            dolphin_process.terminate()

    def init_stats(self):
        self.game_frame = 0
        self.total_frames = 1
        self.skip_frames = 0
        self.thinking_time = 0

    def print_stats(self):
        total_time = time.time() - self.start_time
        frac_skipped = self.skip_frames / self.total_frames
        frac_thinking = self.thinking_time * 1000 / self.total_frames
        print('Total Time:', total_time)
        print('Total Frames:', self.total_frames)
        print('Average FPS:', self.total_frames / total_time)
        print('Fraction Skipped: {:.6f}'.format(frac_skipped))
        print('Average Thinking Time (ms): {:.6f}'.format(frac_thinking))

    def write_locations(self):
        path = self.user + '/MemoryWatcher/'
        util.makedirs(path)
        print('Writing locations to:', path)
        with open(path + 'Locations.txt', 'w') as f:
            f.write('\n'.join(self.sm.locations()))

    def advance_frame(self):
        # print("advance_frame")
        last_frame = self.state.frame
        
        self.update_state()
        if self.state.frame > last_frame:
            skipped_frames = self.state.frame - last_frame - 1
            if skipped_frames > 0:
                self.skip_frames += skipped_frames
                print("Skipped frames ", skipped_frames)
            self.total_frames += self.state.frame - last_frame
            last_frame = self.state.frame

            start = time.time()
            self.make_action()
            self.thinking_time += time.time() - start

            if self.agent.verbose and self.state.frame % (15 * 60) == 0:
                self.print_stats()
        
        self.mw.advance()

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
    
    def make_action(self):
        #menu = Menu(self.state.menu)
        #print(menu)
        if self.state.menu == Menu.Game.value:
            self.game_frame += 1
            
            if self.debug and self.game_frame % 60 == 0:
              print('action_frame', self.state.players[0].action_frame)
              items = list(util.deepItems(ct.toDict(self.state.players)))
              print('max value', max(items, key=lambda x: abs(x[1])))
            
            if self.game_frame <= 120:
              return # wait for game to properly load
            
            for pid, pad in zip(self.pids, self.pads):
                agent = self.agents[pid]
                if agent:
                    agent.act(self.state, pad)

        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages]]:
            self.game_frame = 0
            self.navigate_menus.move(self.state)
            
            if self.navigate_menus.done():
                for pid, pad in zip(self.pids, self.pads):
                    if self.state.menu == Menu.Stages.value:
                        if self.characters[pid] == 'sheik':
                            pad.press_button(Button.A)
                    else:
                        pad.send_controller(ssbm.RealControllerState.neutral)
        
        elif self.state.menu == Menu.PostGame.value:
            self.spam(Button.START)
        else:
            print("Weird menu state", self.state.menu)

def runCPU(**kwargs):
  CPU(**kwargs).run()

