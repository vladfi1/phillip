import ssbm
from state import *
import state_manager
import memory_watcher
import menu_manager
import os
import pad
import time
import fox
import agent
import util
from ctype_util import copy

class CPU:
    def __init__(self, dump=True, dump_seconds=60, dump_dir='experience/', dump_max=20, act_every=1):
        self.dump = dump
        if dump:
          self.dump_dir = dump_dir
          self.dump_max = dump_max
          self.dump_size = 60 * dump_seconds // act_every
          self.dump_state_actions = [(ssbm.GameMemory(), ssbm.SimpleControllerState()) for i in range(self.dump_size)]
          
          self.dump_frame = 0
          self.dump_count = 0
        
        self.first_frame = True
        self.last_acted_frame = 0
        self.act_every = act_every
        self.toggle = False

        # TODO This might not always be accurate.
        dolphin_dir = os.path.expanduser('~/.local/share/dolphin-emu')

        self.state = ssbm.GameMemory()
        self.sm = state_manager.StateManager([0, 1])
        self.write_locations(dolphin_dir)

        self.fox = fox.Fox()
        self.agent = agent.Agent(reload_every=60*dump_seconds//act_every)
        self.mm = menu_manager.MenuManager()

        try:
            print('Creating MemoryWatcher.')
            self.mw = memory_watcher.MemoryWatcher(dolphin_dir + '/MemoryWatcher/MemoryWatcher')
            print('Creating Pad. Open dolphin now.')
            self.pad = pad.Pad(dolphin_dir + '/Pipes/phillip')
            self.initialized = True
        except KeyboardInterrupt:
            self.initialized = False

        self.init_stats()

    def run(self):
        if not self.initialized:
            return
        print('Starting run loop.')
        self.start_time = time.time()
        try:
            while True:
                self.advance_frame()
        except KeyboardInterrupt:
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

    def write_locations(self, dolphin_dir):
        path = dolphin_dir + '/MemoryWatcher/Locations.txt'
        print('Writing locations to:', path)
        with open(path, 'w') as f:
            f.write('\n'.join(self.sm.locations()))

    def dump_state(self):
        state, action = self.dump_state_actions[self.dump_frame]
        copy(self.state, state)
        copy(self.agent.simple_controller, action)

        self.dump_frame += 1

        if self.dump_frame == self.dump_size:
            dump_path = self.dump_dir + str(self.dump_count % self.dump_max)
            print("Dumping to ", dump_path)
            ssbm.writeStateActions(dump_path, self.dump_state_actions)
            self.dump_count += 1
            self.dump_frame = 0

    def advance_frame(self):
        last_frame = self.state.frame
        if self.update_state():
            if self.first_frame:
                self.first_frame = False
            elif self.state.frame > last_frame:
                skipped_frames = self.state.frame - last_frame - 1
                if skipped_frames > 0:
                    self.skip_frames += skipped_frames
                    print("Skipped frames ", skipped_frames)
                self.total_frames += self.state.frame - last_frame
                last_frame = self.state.frame
                
                if self.state.frame - self.last_acted_frame >= self.act_every:
                    start = time.time()
                    self.make_action()
                    self.thinking_time += time.time() - start
                    self.last_acted_frame = self.state.frame

    def update_state(self):
        res = next(self.mw)
        if res is not None:
            self.sm.handle(self.state, *res)
            return True
        return False

    def make_action(self):
        menu = Menu(self.state.menu)
        print(menu)
        if self.state.menu == Menu.Game.value:
            self.agent.act(self.state, self.pad)
            if self.dump:
                self.dump_state()
            #self.fox.advance(self.state, self.pad)
        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages, Menu.PostGame]]:
            # D_DOWN should be hotkeyed to loading an in-game state
            if self.toggle:
              self.pad.press_button(pad.Button.D_DOWN)
              self.toggle = False
            else:
              self.pad.release_button(pad.Button.D_DOWN)
              self.toggle = True
        else:
            print("Weird menu state", self.state.menu)

