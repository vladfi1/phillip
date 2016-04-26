import tensorflow as tf
import ssbm
import tf_lib as tfl
from numpy import random
import RL

def flip(p):
    return random.binomial(1, p)

alpha = 2.0

def random_stick(x):
    a = alpha * x
    return random.beta(a, alpha - a)

def get_controller(action):
    controller = ssbm.RealControllerState()

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

def sample_one_hot_struct(struct):
    fields = [f for f, _ in type(struct)._fields_]
    probs = [getattr(struct, f) for f in fields]
    probs[-1] = 1 - sum(probs[:-1])
    return random.choice(fields, p=probs)

stick_mappings = {
    'up': (0.5, 1),
    'down': (0.5, 0),
    'left': (0, 0.5),
    'right': (1, 0.5),
    'neutral': (0.5, 0.5),
}

def simple_to_real_controller(simple_controller):
    real_controller = ssbm.RealControllerState()

    button = sample_one_hot_struct(simple_controller.buttons)
    real_controller.button_A = button == 'A'
    real_controller.button_B = button == 'B'
    real_controller.button_X = button == 'X'
    #controller.button_Y = flip(action[3])
    #controller.button_L = flip(action[4])
    #controller.button_R = flip(action[5])

    #controller.trigger_L = flip(action[6])
    #controller.trigger_R = flip(action[7])

    stick = sample_one_hot_struct(simple_controller.stick_MAIN)
    real_controller.stick_MAIN.x, real_controller.stick_MAIN.y = stick_mappings[stick]

    # controller.stick_C.x = random_stick(action[10])
    # controller.stick_C.y = random_stick(action[11])

    return real_controller

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
        "Run the state through the loaded graph. Currently unused."
        feed_dict = tfl.feedCType(ssbm.GameMemory, 'predict/state', state)

        to_remove = []
        for op in feed_dict:
            if op not in self.ops:
                to_remove.append(op)
        for op in to_remove:
            #print("removing", op)
            del feed_dict[op]

        return self.sess.run('predict/action:0', feed_dict)

    # action: [A, none, up, down, left, right, neutral]
    def get_simple_controller(self, action):
        self.simple_controller.buttons.A = action[0]
        self.simple_controller.buttons.none = action[1]
        self.simple_controller.stick_MAIN.up = action[2]
        self.simple_controller.stick_MAIN.down = action[3]
        self.simple_controller.stick_MAIN.left = action[4]
        self.simple_controller.stick_MAIN.right = action[5]
        self.simple_controller.stick_MAIN.neutral = action[6]

    def advance(self, state, pad):
        self.counter += 1

        if self.counter >= self.reload_every:
            #self.load_graph()
            print("RL.restore()")
            RL.restore()
            self.counter = 0

        action = RL.predictAction(state)
        self.get_simple_controller(action)
        #print(self.simple_controller)
        if self.counter % 60 == 0:
            print(self.counter)
            print(self.simple_controller.stick_MAIN)
        pad.send_controller(simple_to_real_controller(self.simple_controller))
