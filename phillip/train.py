import os, sys
import time
from phillip import learner, util, ssbm
from phillip.ac import ActorCritic
from phillip.default import *
import numpy as np
from collections import defaultdict
import nnpy
import resource
import gc
import tensorflow as tf
#from memory_profiler import profile
import netifaces
import random
from random import shuffle

# some helpers for debugging memory leaks

def count_objects():
  counts = defaultdict(int)
  for obj in gc.get_objects():
    counts[type(obj)] += 1
  return counts

def diff_objects(after, before):
  diff = {k: after[k] - before[k] for k in after}
  return {k: i for k, i in diff.items() if i}

class Trainer(Default):
  _options = [
    #Option("debug", action="store_true", help="set debug breakpoint"),
    #Option("-q", "--quiet", action="store_true", help="don't print status messages to stdout"),
    Option("init", action="store_true", help="initialize variables"),

    Option("sweep_limit", type=int, default=-1),
    Option("batch_size", type=int, default=1, help="number of trajectories per batch"),
    Option("batch_steps", type=int, default=1, help="number of gradient steps to take on each batch"),
    Option("min_collect", type=int, default=1, help="minimum number of experiences to collect between sweeps"),
    Option("max_age", type=int, help="how old an experience can be before we discard it"),
    Option("max_kl", type=float, help="how off-policy an experience can be before we discard it"),
    Option("max_buffer", type=int, help="maximum size of experience buffer"),
    
    Option("log_interval", type=int, default=10),
    Option("dump", type=str, default="lo", help="interface to listen on for experience dumps"),
    Option('send', type=int, default=1, help="send the network parameters on an nnpy PUB socket"),
    Option("save_interval", type=float, default=10, help="length of time between saves to disk, in minutes"),

    Option("load", type=str, help="path to a json file from which to load params"),
    Option("pop_size", type=int, default=0),
    Option('evolve', action="store_true", help="evolve population"),
    Option("evo_period", type=int, default=1000, help="evolution period"),
    Option("reward_cutoff", type=float, default=1e-3),

    Option('objgraph', type=int, default=0, help='use objgraph to track memory usage'),
    Option('diff_objects', action='store_true', help='print new objects on each iteration')
  ]
  
  _members = [
    ("model", learner.Learner),
  ]
  
  def __init__(self, load=None, **kwargs):
    if load is None:
      args = {}
    else:
      args = util.load_params(load, 'train')
    
    util.pp.pprint(args)
    Default.__init__(self, **args)

    addresses = netifaces.ifaddresses(self.dump)
    address = addresses[netifaces.AF_INET][0]['addr']

    util.makedirs(self.model.path)
    with open(os.path.join(self.model.path, 'ip'), 'w') as f:
      f.write(address)

    self.experience_socket = nnpy.Socket(nnpy.AF_SP, nnpy.PULL)
    experience_addr = "tcp://%s:%d" % (address, util.port(self.model.path + "/experience"))
    self.experience_socket.bind(experience_addr)

    if self.send:
      self.params_socket = nnpy.Socket(nnpy.AF_SP, nnpy.PUB)
      params_addr = "tcp://%s:%d" % (address, util.port(self.model.path + "/params"))
      print("Binding params socket to", params_addr)
      self.params_socket.bind(params_addr)

    self.sweep_size = self.batch_size
    print("Sweep size", self.sweep_size)
    
    if self.init:
      self.model.init()
      self.model.save()
    else:
      self.model.restore()
    
    self.last_save = time.time()
  
  def save(self):
    current_time = time.time()
    
    if current_time - self.last_save > 60 * self.save_interval:
      try:
        self.model.save()
        self.last_save = current_time
      except tf.errors.InternalError as e:
        print(e, file=sys.stderr)

  def selection(self):
    reward = self.model.get_reward()
    print("Evolving. Current reward %f" % reward)
    
    target_id = random.randint(0, self.pop_size-2)
    if target_id >= self.model.pop_id:
      target_id += 1
    print("Selection candidate: %d" % target_id)
    
    target_path = os.path.join(self.model.root, str(target_id))
    latest_ckpt = tf.train.latest_checkpoint(target_path)
    reader = tf.train.NewCheckpointReader(latest_ckpt)
    target_reward = reader.get_tensor('avg_reward')
    
    if target_reward - reward < self.reward_cutoff:
      print("Target reward %f too low." % target_reward)
      return False
    
    print("Selecting %d" % target_id)
    self.model.restore(latest_ckpt)
    return True

  def train(self):
    before = count_objects()

    sweeps = 0
    step = 0
    global_step = self.model.get_global_step()
    
    times = ['min_collect', 'extra_collect', 'train', 'save']
    averages = {name: util.MovingAverage(.9) for name in times}
    
    timer = util.Timer()
    def split(name):
      averages[name].append(timer.split())
    
    experiences = []
    
    while sweeps != self.sweep_limit:
      sweeps += 1
      timer.reset()
      
      #print('Start: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      old_len = len(experiences)
      if self.max_age is not None:
        # print("global_step", global_step)
        age_limit = global_step - self.max_age
        is_valid = lambda exp: exp['global_step'] >= age_limit
        experiences = list(filter(is_valid, experiences))
      else:
        is_valid = lambda _: True
      dropped = old_len - len(experiences)
      
      def pull_experience(block=True):
        exp = self.experience_socket.recv(flags=0 if block else nnpy.DONTWAIT)
        return pickle.loads(exp)

      to_collect = max(self.sweep_size - len(experiences), self.min_collect)
      new_experiences = []

      # print("Collecting experiences", len(experiences))
      doa = 0 # dead on arrival
      while len(new_experiences) < to_collect:
        #print("Waiting for experience")
        exp = pull_experience()
        if is_valid(exp):
          new_experiences.append(exp)
        else:
          #print("dead on arrival", doa)
          doa += 1

      split('min_collect')
      #print('min_collected')

      # pull in all the extra experiences
      for _ in range(self.sweep_size):
        try:
          exp = pull_experience(False)
          if is_valid(exp):
            new_experiences.append(exp)
          else:
            doa += 1
        except nnpy.NNError as e:
          if e.error_no == nnpy.EAGAIN:
            # nothing to receive
            break
          # a real error
          raise e

      experiences += new_experiences
      
      ages = np.array([global_step - exp['global_step'] for exp in experiences])
      print("Mean age:", ages.mean())
            
      #print('After collect: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      split('extra_collect')
      
      #shuffle(experiences)

      batches = len(experiences) // self.batch_size
      batch_size = (len(experiences) + batches - 1) // batches
      
      kls = []

      try:
        for batch in util.chunk(experiences, batch_size):
          train_out = self.model.train(batch, self.batch_steps,
                                       log=(step%self.log_interval==0),
                                       retrieve_kls=True)[-1]
          global_step = train_out['global_step']
          kls.extend(train_out['kls'].tolist())
          step += 1
      except tf.errors.InvalidArgumentError as e:
        # always a NaN in histogram summary for entropy - what's up with that?
        experiences = []
        print(e)
        continue
      
      print("Mean KL", np.mean(kls))

      old_len = len(experiences)
      kl_exps = zip(kls, experiences)
      if self.max_buffer and old_len > self.max_buffer:
        kl_exps = list(kl_exps)[-self.max_buffer:]
      if self.max_kl:
        kl_exps = [ke for ke in kl_exps if ke[0] <= self.max_kl]
      kls, experiences = zip(*kl_exps)
      experiences = list(experiences)
      dropped += old_len - len(experiences)
      
      #print('After train: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      split('train')

      if self.evolve and sweeps % self.evo_period == 0:
        if self.selection():
          experiences = []
        self.model.mutation()

      if self.send:
        #self.params_socket.send_string("", zmq.SNDMORE)
        params = self.model.blob()
        blob = pickle.dumps(params)
        #print('After blob: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.params_socket.send(blob)
        #print('After send: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      self.save()
      
      #print('After save: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      split('save')
      
      if self.diff_objects:
        after = count_objects()
        print(diff_objects(after, before))
        before = after
      
      time_avgs = [averages[name].avg for name in times]
      total_time = sum(time_avgs)
      time_avgs = ['%.3f' % (t / total_time) for t in time_avgs]
      print(sweeps, len(experiences), len(new_experiences), dropped, doa, total_time, *time_avgs)
      print('Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

      if self.objgraph:
        import objgraph
        #gc.collect()  # don't care about stuff that would be garbage collected properly
        objgraph.show_growth()
  
  def fake_train(self):
    experience = (ssbm.SimpleStateAction * self.model.config.experience_length)()
    experience = ssbm.prepareStateActions(experience)
    experience['initial'] = util.deepMap(np.zeros, self.model.core.hidden_size)
    
    experiences = [experience] * self.batch_size
    
    # For more advanced usage, user can control the tracing steps and
    # dumping steps. User can also run online profiling during training.
    #
    # Create options to profile time/memory as well as parameters.
    builder = tf.profiler.ProfileOptionBuilder
    opts = builder(builder.time_and_memory()).order_by('micros').build()
    opts2 = tf.profiler.ProfileOptionBuilder.trainable_variables_parameter()

    # Collect traces of steps 10~20, dump the whole profile (with traces of
    # step 10~20) at step 20. The dumped profile can be used for further profiling
    # with command line interface or Web UI.
    with tf.contrib.tfprof.ProfileContext('/tmp/train_dir',
                                          trace_steps=range(10, 20),
                                          dump_steps=[20]) as pctx:
      # Run online profiling with 'op' view and 'opts' options at step 15, 18, 20.
      pctx.add_auto_profiling('op', opts, [15, 18, 20])
      # Run online profiling with 'scope' view and 'opts2' options at step 20.
      pctx.add_auto_profiling('scope', opts2, [20])
      # High level API, such as slim, Estimator, etc.
      count = 0
      while count != self.sweep_limit:
        self.model.train(experiences, self.batch_steps)
        count += 1

if __name__ == '__main__':
  from argparse import ArgumentParser
  parser = ArgumentParser()

  for opt in Trainer.full_opts():
    opt.update_parser(parser)

  for opt in ActorCritic.full_opts():
    opt.update_parser(parser)
      
  parser.add_argument('--fake', action='store_true', help='Train on fake experiences for debugging.')

  args = parser.parse_args()
  trainer = Trainer(**args.__dict__)
  if args.fake:
    trainer.fake_train()
  else:
    trainer.train()

