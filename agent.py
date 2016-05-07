import tensorflow as tf
import ssbm
import tf_lib as tfl
from numpy import random
import RL

def flip(p):
    return random.binomial(1, p)

class Agent:
    def __init__(self, graph_path='models/simpleDQN.pb', reload_every=60*60,
        name='simpleDQN', seed=None):
        self.graph_path = graph_path
        #self.sess = None
        #self.load_graph()
        self.name = name
        self.reload_every = reload_every
        self.counter = 0
        self.simple_controller = ssbm.SimpleControllerState()
        RL.restore(self.name)
        
        if seed is not None:
            random.seed(seed)

    def load_graph(self):
        print("loading ", self.graph_path)

        graph_def = tf.GraphDef()
        with open(self.graph_path, 'rb') as f:
            graph_def.ParseFromString(f.read())

        with tf.Graph().as_default() as imported_graph:
            tf.import_graph_def(graph_def, name='')
            self.sess = tf.Session(graph=imported_graph)

        # TODO: precompute which ops are necessary
        self.ops = set([op.name + ':0' for op in self.sess.graph.get_operations()])

    def epsilon_greedy(self, state):
        scores = RL.scoreActions(state)
        self.scores = scores

        score, best_action = max(zip(scores, ssbm.simpleControllerStates), key=lambda x: x[0])
        #print(score, best_action)

        #self.epsilon = RL.getEpsilon()
        self.epsilon = 0.02

        if flip(self.epsilon):
            self.simple_controller = ssbm.SimpleControllerState.randomValue()
        else:
            self.simple_controller = best_action

    def get_action(self, state):
        if flip(0.02):
            self.probs = None
        else:
            self.probs = RL.getActionProbs(state)
            # numpy does weird things to ctypes?
        index = random.choice(range(len(ssbm.simpleControllerStates)), p=self.probs)
        self.simple_controller = ssbm.simpleControllerStates[index]

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
            print("Scores", RL.scoreActions(state))
            print("Temp", RL.getTemperature())
            print("Probs", RL.getActionProbs(state))
            print(self.simple_controller)
        pad.send_controller(self.simple_controller.realController())
