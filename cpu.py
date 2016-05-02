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
from ctype_util import copy, clone
import RL

default_args = dict(
    name='simpleDQN',
    dump = True,
    dump_seconds = 60,
    dump_max = 1000,
    act_every = 5,
    num_agents = 1,
    # TODO This might not always be accurate.
    dolphin_dir = '~/.local/share/dolphin-emu',
)

def switch_players(state, a, b):
    swapped_state = clone(state)
    swapped_state.players[a] = state.players[b]
    swapped_state.players[b] = state.players[a]
    return swapped_state

class CPU:
    def __init__(self, **args):
        for k, v in default_args.items():
            if k in args and args[k] is not None:
                setattr(self, k, args[k])
            else:
                setattr(self, k, v)

        if self.dump:
            self.dump_dir = "saves/" + self.name + "/experience/"
            self.dump_size = 60 * self.dump_seconds // self.act_every
            self.dump_state_actions = [[(ssbm.GameMemory(), ssbm.SimpleControllerState()) for i in range(self.dump_size)]
                for j in range(self.num_agents)]

            self.dump_frame = 0
            self.dump_count = 0

        self.reward_logfile = 'saves/' + self.name + '/rewards.log'
        self.first_frame = True
        self.last_acted_frame = 0
        self.toggle = False

        self.dolphin_dir = os.path.expanduser(self.dolphin_dir)

        self.state = ssbm.GameMemory()
        self.sm = state_manager.StateManager([0, 1])
        self.write_locations(self.dolphin_dir)

        self.counter = 0
        self.reload_every = 60*self.dump_seconds//self.act_every

        self.fox = fox.Fox()
        self.agents = [agent.Agent(name=self.name)
            for i in range(self.num_agents)]
        self.mm = menu_manager.MenuManager()

        try:
            print('Creating MemoryWatcher.')
            self.mw = memory_watcher.MemoryWatcher(self.dolphin_dir + '/MemoryWatcher/MemoryWatcher')
            print('Creating Pad. Open dolphin now.')

            # self.pad = pad.Pad(self.dolphin_dir + '/Pipes/phillip')
            self.pads = [pad.Pad(self.dolphin_dir + '/Pipes/phillip' + str(i))
                for i in range(self.num_agents)]
            for current_pad in self.pads:
                current_pad.send_controller(ssbm.NeutralControllerState)

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
        for agent_index, agent in enumerate(self.agents):
            state, action = self.dump_state_actions[agent_index][self.dump_frame]
            swapped_state = switch_players(self.state, 1, agent_index)
            copy(swapped_state, state)
            copy(agent.simple_controller, action)

        self.dump_frame += 1

        if self.dump_frame == self.dump_size:
            for agent_index in range(len(self.agents)):
                dump_path = self.dump_dir + str(self.dump_count % self.dump_max)
                print("Dumping to ", dump_path)
                ssbm.writeStateActions(dump_path,
                    self.dump_state_actions[agent_index])
                self.dump_count += 1
                self.dump_frame = 0

            rewards = RL.computeRewards([memory[0]
                for memory in self.dump_state_actions[0]])

            with open(self.reward_logfile, 'a') as f:
                f.write(str(sum(rewards) / len(rewards)) + "\n")
                f.flush()


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
        # menu = Menu(self.state.menu)
        # print(menu)

        if self.state.menu == Menu.Game.value:
            self.counter += 1
            for agent_index in range(len(self.agents)):
                # import pdb; pdb.set_trace()
                swapped_state = switch_players(self.state, 1, agent_index)
                self.agents[agent_index].act(swapped_state,
                    self.pads[agent_index])

                # for current_pad in self.pads:
                #     current_pad.send_controller(ssbm.NeutralControllerState)
                    # current_pad.press_trigger(pad.Trigger.L, -2)
                    # current_pad.press_trigger(pad.Trigger.R, -2)

            if self.dump:
                self.dump_state()

            if self.counter >= self.reload_every:
                print("RL.restore()-ing " + self.name)
                RL.restore(self.name)
                self.counter = 0

            #self.fox.advance(self.state, self.pad)

        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages]]:
            # D_DOWN should be hotkeyed to loading an in-game state

            # # self.pad.send_controller(ssbm.NeutralControllerState)

            if self.toggle:
              self.pads[0].press_button(pad.Button.D_DOWN)
              self.toggle = False
            else:
              self.pads[0].release_button(pad.Button.D_DOWN)
              self.toggle = True

        elif self.state.menu in [menu.value for menu in [Menu.PostGame]]:
            if self.toggle:
              self.pads[0].press_button(pad.Button.START)
              self.toggle = False
            else:
              self.pads[0].release_button(pad.Button.START)
              self.toggle = True

        elif self.state.menu in [menu.value for menu in [Menu.Characters, Menu.Stages, Menu.PostGame]]:
            # wait for the movie to get us into the game
            pass
        else:
            print("Weird menu state", self.state.menu)
