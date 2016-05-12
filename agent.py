import tensorflow as tf
import ssbm
import tf_lib as tfl
from numpy import random, exp
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
        self.simple_controller = ssbm.simpleControllerStates[0]
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

        score, best_action = max(zip(scores, ssbm.simpleControllerStates), key=lambda x: x[0])
        #print(score, best_action)

        #self.epsilon = RL.getEpsilon()
        self.epsilon = 0.05

        if flip(self.epsilon):
            index = random.choice(range(len(scores)))
            self.simple_controller = ssbm.SimpleControllerState.fromIndex(index)
        else:
            self.simple_controller = best_action

        if self.counter % 60 == 0:
            print(state.players[1])
            print("Scores", scores)
            print("Epsilon", self.epsilon)
            print(self.simple_controller)

    def softmax(self, state):
        probs = RL.getActionProbs(state)
        index = random.choice(range(len(probs)), p=probs)
        self.simple_controller = ssbm.SimpleControllerState.fromIndex(index)

        if self.counter % 60 == 0:
            print(state.players[1])
            print("Probs", probs)
            print(self.simple_controller)

    def thompson(self, state):
        self.dists = list(zip(*RL.getActionDists(state)))

        samples = [random.normal(m, exp(v/2.0)) for m, v in self.dists]

        self.simple_controller = max(zip(samples, ssbm.simpleControllerStates), key=lambda x: x[0])[1]

        if self.counter % 60 == 0:
            print(state.players[1])
            print("Dists", self.dists)
            print(self.simple_controller)

    def act(self, state, pad):
        self.counter += 1

        if self.counter >= self.reload_every:
            #self.load_graph()
            print("RL.restore()-ing " + self.name)
            RL.restore(self.name)
            self.counter = 0

        #self.thompson(state)
        #self.epsilon_greedy(state)
        self.softmax(state)

        pad.send_controller(self.simple_controller.realController())
