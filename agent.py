import tensorflow as tf
import ssbm
import tf_lib as tfl
from numpy import random
import RL

def flip(p):
    return random.binomial(1, p)

class Agent:
    def __init__(self, graph_path='models/simpleDQN.pb', reload_every=60*60,
        name='simpleDQN'):
        self.graph_path = graph_path
        #self.sess = None
        #self.load_graph()
        self.name = name
        self.sample = True
        self.reload_every = reload_every
        self.counter = 0
        self.simple_controller = ssbm.SimpleControllerState()
        RL.restore(self.name)

    def load_graph(self):
        print("loading ", self.graph_path)

        graph_def = tf.GraphDef()
        with open(self.graph_path, 'rb') as f:
            graph_def.ParseFromString(f.read())

        with tf.Graph().as_default() as imported_graph:
            tf.import_graph_def(graph_def, name='')
            self.sess = tf.Session(graph=imported_graph)

        # TODO: precompute which ops are necessary
        self.ops = set([op.name + ':0'
                        for op in self.sess.graph.get_operations()])

    def get_action(self, state):
        scores = RL.getActions(state)
        self.scores = scores
        self.epsilon = 0.02


        if self.sample:
            # import ipdb; ipdb.set_trace()
            scores = scores[0]
            stick = random.choice([s for s in ssbm.SimpleStick], p=scores[:5])
            button = random.choice([s for s in ssbm.SimpleButton], p=scores[5:])
            self.simple_controller = ssbm.SimpleControllerState(
                button=button,
                stick_MAIN=stick)
        else:
            scored_actions = zip(scores, ssbm.simpleControllerStates)
            score, best_action = max(
                                     scored_actions,
                                     key=lambda x: x[0])
            if flip(self.epsilon):
                self.simple_controller = ssbm.SimpleControllerState.randomValue()
            else:
                self.simple_controller = best_action


    def act(self, state, pad):
        self.counter += 1

        if self.counter >= self.reload_every:
            #self.load_graph()
            print("RL.restore()-ing " + self.name)
            RL.restore(self.name)
            self.counter = 0

        self.get_action(state)
        if self.counter % 60 == 0:
            print("Frame %d of recording." % self.counter)
            print(state.players[1])
            print("Scores", self.scores)
            print(self.simple_controller)
            print("epsilon: ", self.epsilon)
        pad.send_controller(self.simple_controller.realController())
