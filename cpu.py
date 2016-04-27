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

class CPU:
    def __init__(self, dump=True, dump_size=3600, dump_dir='experience/', dump_max=20):
        self.dump = dump
        self.dump_size = dump_size
        self.dump_dir = dump_dir
        self.dump_max = dump_max

        # TODO This might not always be accurate.
        dolphin_dir = os.path.expanduser('~/.local/share/dolphin-emu')

        self.state = ssbm.GameMemory()
        self.sm = state_manager.StateManager([0, 1])
        self.write_locations(dolphin_dir)

        self.fox = fox.Fox()
        self.agent = agent.Agent()
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
        try:
            while True:
                self.advance_frame()
        except KeyboardInterrupt:
            self.print_stats()

    def init_stats(self):
        self.total_frames = 0
        self.skip_frames = 0
        self.thinking_time = 0

        self.dump_frame = 0
        self.dump_count = 0

    def print_stats(self):
        frac_skipped = self.skip_frames / self.total_frames
        frac_thinking = self.thinking_time * 1000 / self.total_frames
        print('Total Frames:', self.total_frames)
        print('Fraction Skipped: {:.6f}'.format(frac_skipped))
        print('Average Thinking Time (ms): {:.6f}'.format(frac_thinking))

    def write_locations(self, dolphin_dir):
        path = dolphin_dir + '/MemoryWatcher/Locations.txt'
        print('Writing locations to:', path)
        with open(path, 'w') as f:
            f.write('\n'.join(self.sm.locations()))

    def dump_state(self):
        if self.dump_frame == 0:
            # pre-allocate/reuse space?
            self.dump_array = bytearray()

        self.dump_array.extend(self.state)
        self.dump_array.extend(self.agent.simple_controller)

        self.dump_frame += 1

        if self.dump_frame == self.dump_size:
            dump_path = self.dump_dir + str(self.dump_count % self.dump_max)
            print("Dumping to ", dump_path)
            with open(dump_path, 'wb') as f:
                f.write(self.dump_array)
            self.dump_count += 1
            self.dump_frame = 0

    def advance_frame(self):
        last_frame = self.state.frame
        if self.update_state():
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

    def update_state(self):
        res = next(self.mw)
        if res is not None:
            self.sm.handle(self.state, *res)
            return True
        return False

    def make_action(self):
        #menu = state.Menu(self.state.menu)
        #print (menu)
        if self.state.menu == Menu.Game.value:
            if self.dump:
                self.dump_state()
            #self.fox.advance(self.state, self.pad)
            self.agent.advance(self.state, self.pad)
        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages, Menu.PostGame]]:
            # this should be kotkeyed to loading an in-game state
            if self.state.frame % 2:
              self.pad.press_button(pad.Button.D_DOWN)
            else:
              self.pad.release_button(pad.Button.D_DOWN)
        else:
            print("Weird menu state", self.state.menu)

