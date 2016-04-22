import tensorflow as tf
import ssbm
import tf_lib as tfl
from numpy import random

def flip(p):
    return random.binomial(1, p)

alpha = 2.0

def random_stick(x):
    a = alpha * x
    return random.beta(a, alpha - a)

def get_controller(action):
    controller = ssbm.ControllerState()
    
    controller.button_A = flip(action[0])
    controller.button_B = flip(action[1])
    controller.button_X = flip(action[2])
    #controller.button_Y = flip(action[3])
    #controller.button_L = flip(action[4])
    #controller.button_R = flip(action[5])

    #controller.trigger_L = flip(action[6])
    #controller.trigger_R = flip(action[7])
    
    controller.stick_MAIN.x = random_stick(action[8])
    controller.stick_MAIN.y = random_stick(action[9])
    
    controller.stick_C.x = random_stick(action[10])
    controller.stick_C.y = random_stick(action[11])
    
    return controller
  
class Agent:
    def __init__(self, graph_path='models/simpleDQN.pb', reload_every=60*60):
        self.graph_path = graph_path
        self.sess = None
        self.load_graph()
        self.reload_every = reload_every
        self.counter = 0
    
    def load_graph(self):
        if self.sess is not None:
            self.sess.close()
        graph_def = tf.GraphDef()
        with open(self.graph_path, 'rb') as f:
            graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name='')
        self.sess = tf.Session()
        # TODO: precompute which ops are necessary
        self.ops = set([op.name + ':0' for op in self.sess.graph.get_operations()])
    
    def advance(self, state, pad):
        self.counter += 1
        
        if self.counter >= self.reload_every:
            self.load_graph()
            self.counter = 0
        
        feed_dict = tfl.feedCType(ssbm.GameMemory, 'predict/state', state)
        
        to_remove = []
        for op in feed_dict:
            if op not in self.ops:
                to_remove.append(op)
        for op in to_remove:
            #print("removing", op)
            del feed_dict[op]
        
        action = self.sess.run('predict/action:0', feed_dict)
        pad.send_controller(get_controller(action))
