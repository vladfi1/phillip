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
from reward import computeRewards

default_args = dict(
    path=None,
    tag=None,
    dump = True,
    dump_max = 10,
    # TODO This might not always be accurate.
    dolphin_dir = '~/.local/share/dolphin-emu/',
    self_play = None,
    model="DQN",
)

class CPU:
    def __init__(self, **kwargs):
        for k, v in default_args.items():
            if k in kwargs and kwargs[k] is not None:
                setattr(self, k, kwargs[k])
            else:
                setattr(self, k, v)

        if self.dump:
            self.dump_dir = self.path + "/experience/"
            os.makedirs(self.dump_dir, exist_ok=True)
            self.dump_tag = "" if self.tag is None else str(self.tag) + "-"
            self.dump_size = experience_length
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
        
        self.cpus = [0, 1] if self.self_play else [1]
        self.agents = []

        reload_every = experience_length
        if self.self_play:
            self.enemy = agent.Agent(reload_every=self.self_play*reload_every, swap=True, **kwargs)
            self.agents.append(self.enemy)
        self.agent = agent.Agent(reload_every=reload_every, **kwargs)
        self.agents.append(self.agent)
        
        self.mm = menu_manager.MenuManager()

        print('Creating MemoryWatcher.')
        self.mw = memory_watcher.MemoryWatcher(self.dolphin_dir + '/MemoryWatcher/MemoryWatcher')
        
        pipe_dir = self.dolphin_dir + '/Pipes/'
        print('Creating Pads at %s. Open dolphin now.' % pipe_dir)
        os.makedirs(self.dolphin_dir + '/Pipes/', exist_ok=True)
        
        paths = [pipe_dir + 'phillip%d' % i for i in self.cpus]
        self.get_pads = util.async_map(pad.Pad, paths)

        self.init_stats()

    def run(self, frames=None, dolphin_process=None):
        try:
            self.pads = self.get_pads()
        except KeyboardInterrupt:
            print("Pipes not initialized!")
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
            if self.dump_count == 0:
            # if False:
                dump_path = self.dump_dir + ".dead"
            else:
                dump_path = self.dump_dir + self.dump_tag + str(self.dump_count % self.dump_max)
            print("Dumping to ", dump_path)
            #ssbm.writeStateActions(dump_path, self.dump_state_actions)
            ssbm.writeStateActions_pickle(dump_path, self.dump_state_actions)
            self.dump_count += 1
            self.dump_frame = 0

            rewards = computeRewards(self.dump_state_actions)

            with open(self.reward_logfile, 'a') as f:
                f.write(str(time.time()) + " " + str(sum(rewards) / len(rewards)) + "\n")
                f.flush()

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

            if self.state.frame % (15 * fps) == 0:
                self.print_stats()
        
        self.mw.advance()

    def update_state(self):
        messages = self.mw.get_messages()
        for message in messages:
          self.sm.handle(self.state, *message)

    def make_action(self):
        # menu = Menu(self.state.menu)
        # print(menu)
        if self.state.menu == Menu.Game.value:
            if self.action_counter % act_every == 0:
                for agent, pad in zip(self.agents, self.pads):
                    agent.act(self.state, pad)
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

def runCPU(**kwargs):
  CPU(**kwargs).run()

