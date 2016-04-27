import tensorflow as tf
import ssbm
import tf_lib as tfl
from numpy import random
import RL

def flip(p):
    return random.binomial(1, p)

class Agent:
    def __init__(self, graph_path='models/simpleDQN.pb', reload_every=60*60):
        self.graph_path = graph_path
        #self.sess = None
        #self.load_graph()
        self.reload_every = reload_every
        self.counter = 0
        self.simple_controller = ssbm.SimpleControllerState()
        RL.restore()

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
    
    def get_action(self, state):
        scores = RL.scoreActions(state)
        
        score, best_action = max(zip(scores, ssbm.simpleControllerStates), key=lambda x: x[0])
        #print(score, best_action)
        
        epsilon = 0.5
        
        if flip(epsilon):
          self.simple_controller = ssbm.SimpleControllerState.randomValue()
        else:
          self.simple_controller = best_action

    def advance(self, state, pad):
        self.counter += 1

        if self.counter >= self.reload_every:
            #self.load_graph()
            print("RL.restore()")
            RL.restore()
            self.counter = 0

        self.get_action(state)
        if self.counter % 60 == 0:
            print("Frame %d of recording." % self.counter)
            print(self.simple_controller)
        pad.send_controller(self.simple_controller.realController())
