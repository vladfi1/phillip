import ssbm
from state import *
import state_manager
import memory_watcher
from menu_manager import *
import os
from pad import *
import time
import fox
import agent
import util
from ctype_util import copy
import RL
from numpy import random
from reward import computeRewards
import movie
from default import *

class CPU(Default):
    _options = [
      Option('tag', type=int),
      Option('dump', type=str, help="dump experiences to ip address via zmq"),
      Option('user', type=str, help="dolphin user directory"),
      Option('zmq', type=bool, default=True, help="use zmq for memory watcher"),
      Option('stage', type=str, default="final_destination", choices=movie.stages.keys(), help="which stage to play on"),
      Option('enemy', type=str, help="load enemy agent from file"),
      Option('enemy_reload', type=int, default=0, help="enemy reload interval"),
    ] + [Option('p%d' % i, type=str, choices=characters.keys(), default="falcon", help="character for player %d" % i) for i in [1, 2]]
    
    _members = [
      ('agent', agent.Agent),
    ]
    
    def __init__(self, **kwargs):
        Default.__init__(self, **kwargs)
        
        self.model = self.agent.model
        self.rlConfig = self.model.rlConfig
        
        if self.dump:
            try:
              import zmq
            except ImportError as err:
              print("ImportError: {0}".format(err))
              sys.exit("Install pyzmq to dump experiences")
            
            context = zmq.Context()

            self.socket = context.socket(zmq.PUSH)
            self.sock_addr = "tcp://%s:%d" % (self.dump, util.port(self.model.name))
            print("Connecting to " + self.sock_addr)
            self.socket.connect(self.sock_addr)
            
            self.dump_size = self.rlConfig.experience_length
            self.dump_state_actions = (self.dump_size * ssbm.SimpleStateAction)()
  
            self.dump_frame = 0
            self.dump_count = 0

        self.first_frame = True
        self.action_counter = 0
        self.toggle = False

        self.user = os.path.expanduser(self.user)

        self.state = ssbm.GameMemory()
        # track players 1 and 2 (pids 0 and 1)
        self.sm = state_manager.StateManager([0, 1])
        self.write_locations()

        if self.tag is not None:
            random.seed(self.tag)
        
        self.pids = [1]
        self.agents = {1: self.agent}
        self.characters = {1: self.agent.char or self.p2}

        reload_every = self.rlConfig.experience_length
        self.agent.reload_every = reload_every
        
        if self.enemy:
            with open(self.enemy + 'params', 'r') as f:
                import json
                enemy_kwargs = json.load(f)['agent']
            enemy_kwargs.update(
                reload_every=self.enemy_reload * reload_every,
                swap=True,
                dump=None,
                path=self.enemy
            )
            enemy = agent.Agent(**enemy_kwargs)
        
            self.pids.append(0)
            self.agents[0] = enemy
            self.characters[0] = enemy.char or self.p1
        
        self.menu_managers = {i: MenuManager(characters[c], pid=i) for i, c in self.characters.items()}

        print('Creating MemoryWatcher.')
        mwType = memory_watcher.MemoryWatcher
        if self.zmq:
          mwType = memory_watcher.MemoryWatcherZMQ
        self.mw = mwType(self.user + '/MemoryWatcher/MemoryWatcher')
        
        pipe_dir = self.user + '/Pipes/'
        print('Creating Pads at %s. Open dolphin now.' % pipe_dir)
        util.makedirs(self.user + '/Pipes/')
        
        paths = [pipe_dir + 'phillip%d' % i for i in self.pids]
        self.get_pads = util.async_map(Pad, paths)

        self.init_stats()
        
        # sets the game mode and random stage
        self.movie = movie.Movie(movie.endless_netplay + movie.stages[self.stage])

    def run(self, frames=None, dolphin_process=None):
        try:
            self.pads = self.get_pads()
        except KeyboardInterrupt:
            print("Pipes not initialized!")
            return

        for pid, pad in zip(self.pids, self.pads):
            self.menu_managers[pid].pad = pad
        
        self.settings_mm = MenuManager(settings, pid=self.pids[0], pad=self.pads[0])
        
        print('Starting run loop.')
        self.start_time = time.time()
        try:
            while True:
                self.advance_frame()
        except KeyboardInterrupt:
            if dolphin_process is not None:
                dolphin_process.terminate()
            self.print_stats()

    def init_stats(self):
        self.total_frames = 0
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

    def dump_state(self):
        state_action = self.dump_state_actions[self.dump_frame]
        state_action.state = self.state
        state_action.prev = self.agent.prev_action
        state_action.action = self.agent.action

        self.dump_frame += 1

        if self.dump_frame == self.dump_size:
            self.dump_count += 1
            self.dump_frame = 0
            
            if self.dump_count == 1:
                return # FIXME
            
            print("Dumping", self.dump_count)
            
            prepared = ssbm.prepareStateActions(self.dump_state_actions)
            
            self.socket.send_pyobj(prepared)

    def advance_frame(self):
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

            if self.state.frame % (15 * 60) == 0:
                self.print_stats()
        
        self.mw.advance()

    def update_state(self):
        messages = self.mw.get_messages()
        for message in messages:
          self.sm.handle(self.state, *message)
    
    def spam(self, button):
        if self.toggle:
            self.pads[0].press_button(button)
            self.toggle = False
        else:
            self.pads[0].release_button(button)
            self.toggle = True
    
    def make_action(self):
        # menu = Menu(self.state.menu)
        # print(menu)
        if self.state.menu == Menu.Game.value:
            if self.action_counter % self.rlConfig.act_every == 0:
                for pid, pad in zip(self.pids, self.pads):
                    self.agents[pid].act(self.state, pad)
                if self.dump:
                    self.dump_state()
            self.action_counter += 1
            #self.fox.advance(self.state, self.pad)

        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages]]:
            # FIXME: this is very convoluted
            done = True
            for mm in self.menu_managers.values():
                if not mm.reached:
                    done = False
                mm.move(self.state)
            
            if done:
                if self.settings_mm.reached:
                    self.movie.play(self.pads[0])
                else:
                    self.settings_mm.move(self.state)
        elif self.state.menu == Menu.PostGame.value:
            self.spam(Button.START)
        else:
            print("Weird menu state", self.state.menu)

def runCPU(**kwargs):
  CPU(**kwargs).run()

