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
import RL
from config import *
from numpy import random

default_args = dict(
    model="DQN",
    path=None,
    tag=None,
    dump = True,
    dump_seconds = 60,
    dump_max = 1000,
    # TODO This might not always be accurate.
    dolphin_dir = '~/.local/share/dolphin-emu/',
)

class CPU:
    def __init__(self, model=None, **args):
        for k, v in default_args.items():
            if k in args and args[k] is not None:
                setattr(self, k, args[k])
            else:
                setattr(self, k, v)

        if self.dump:
            self.dump_dir = self.path + "/experience/"
            os.makedirs(self.dump_dir, exist_ok=True)
            self.dump_tag = "" if self.tag is None else str(self.tag) + "-"
            self.dump_size = 60 * self.dump_seconds // act_every
            self.dump_state_actions = (self.dump_size * ssbm.SimpleStateAction)()

            self.dump_frame = 0
            self.dump_count = 0

        self.reward_logfile = self.path + '/rewards.log'
        self.first_frame = True
        self.action_counter = 0
        self.toggle = False

        self.dolphin_dir = os.path.expanduser(self.dolphin_dir)

        self.state = ssbm.GameMemory()
        self.sm = state_manager.StateManager([0, 1])
        self.write_locations(self.dolphin_dir)

        self.fox = fox.Fox()
        if self.tag is not None:
            random.seed(self.tag)
        self.agent = agent.Agent(model, self.path, reload_every=60*self.dump_seconds//act_every)
        self.mm = menu_manager.MenuManager()

        try:
            print('Creating MemoryWatcher.')
            self.mw = memory_watcher.MemoryWatcher(self.dolphin_dir + '/MemoryWatcher/MemoryWatcher')
            print('Creating Pad. Open dolphin now.')
            os.makedirs(self.dolphin_dir + '/Pipes/', exist_ok=True)
            self.pad = pad.Pad(self.dolphin_dir + '/Pipes/phillip1')
            self.initialized = True
        except KeyboardInterrupt:
            self.initialized = False

        self.init_stats()

    def run(self, dolphin_process=None):
        if not self.initialized:
            print("CPU not initialized!")
            return
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

    def write_locations(self, dolphin_dir):
        path = dolphin_dir + '/MemoryWatcher/'
        os.makedirs(path, exist_ok=True)
        print('Writing locations to:', path)
        with open(path + 'Locations.txt', 'w') as f:
            f.write('\n'.join(self.sm.locations()))

    def dump_state(self):
        state_action = self.dump_state_actions[self.dump_frame]
        state_action.state = self.state
        state_action.action = self.agent.simple_controller.index

        self.dump_frame += 1

        if self.dump_frame == self.dump_size:
            dump_path = self.dump_dir + self.dump_tag + str(self.dump_count % self.dump_max)
            print("Dumping to ", dump_path)
            ssbm.writeStateActions#(dump_path, self.dump_state_actions)
            ssbm.writeStateActions_pickle(dump_path, self.dump_state_actions)
            self.dump_count += 1
            self.dump_frame = 0

            rewards = RL.computeRewards([memory.state
                for memory in self.dump_state_actions])

            with open(self.reward_logfile, 'a') as f:
                f.write(str(sum(rewards) / len(rewards)) + "\n")
                f.flush()

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
                
                if self.state.frame % (15 * fps) == 0:
                    self.print_stats()

    def update_state(self):
        res = next(self.mw)
        if res is not None:
            self.sm.handle(self.state, *res)
            return True
        return False

    def make_action(self):
        # menu = Menu(self.state.menu)
        # print(menu)
        if self.state.menu == Menu.Game.value:
            if self.action_counter % act_every == 0:
                self.agent.act(self.state, self.pad)
                if self.dump:
                    self.dump_state()
            self.action_counter += 1
            #self.fox.advance(self.state, self.pad)

        # elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages]]:
            # D_DOWN should be hotkeyed to loading an in-game state

            # self.pad.send_controller(ssbm.NeutralControllerState)

        #     if self.toggle:
        #       self.pad.press_button(pad.Button.D_DOWN)
        #       self.toggle = False
        #     else:
        #       self.pad.release_button(pad.Button.D_DOWN)
        #       self.toggle = True
        #
        # elif self.state.menu in [menu.value for menu in [Menu.PostGame]]:
        #     if self.toggle:
        #       self.pad.press_button(pad.Button.START)
        #       self.toggle = False
        #     else:
        #       self.pad.release_button(pad.Button.START)
        #       self.toggle = True

        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages, Menu.PostGame]]:
            # print(self.state.players[0].controller)
            # wait for the movie to get us into the game
            pass
        else:
            print("Weird menu state", self.state.menu)
