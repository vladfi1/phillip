from phillip import RL

class Learner(RL.RL):
  def __init__(self, debug=False, **kwargs):
    super(Learner, self).__init__(mode=RL.Mode.LEARNER, debug=debug, **kwargs)

  def train(self, experiences,
            batch_steps=1,
            train=True,
            log=True,
            zipped=False,
            retrieve_kls=False, 
            **kwargs):
    if not zipped:
      experiences = util.deepZip(*experiences)
    
    input_dict = dict(util.deepValues(util.deepZip(self.experience, experiences)))
    
    """
    saved_data = self.sess.run(self.saved_data, input_dict)
    handles = [t.handle for t in saved_data]
    
    saved_dict = dict(zip(self.placeholders, handles))
    """
    
    run_dict = dict(
      global_step = self.global_step,
      misc = self.misc
    )
    
    if train:
      run_dict.update(train=self.train_ops)
    
    if retrieve_kls:
      run_dict.update(kls=self.kls)
    
    if self.profile:
      run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
      run_metadata = tf.RunMetadata()
      print('Profiling enabled, disabling logging!')
      log = False # logging eats time?
    else:
      run_options = None
      run_metadata = None

    if log:
      run_dict.update(summary=self.summarize)
    
    outputs = []
    
    for _ in range(batch_steps):
      try:
        results = self.sess.run(run_dict, input_dict,
            options=run_options, run_metadata=run_metadata)
      except tf.errors.InvalidArgumentError as e:
        import pickle
        with open(os.path.join(self.path, 'error_frame'), 'wb') as f:
          pickle.dump(experiences, f)
        raise e
      #print('After run: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
      
      outputs.append(results)
      global_step = results['global_step']
      if log:
        summary_str = results['summary']
        self.writer.add_summary(summary_str, global_step)
      if self.profile:
        # Create the Timeline object, and write it to a json
        from tensorflow.python.client import timeline
        tl = timeline.Timeline(run_metadata.step_stats)
        ctf = tl.generate_chrome_trace_format()
        path = 'timelines/%s' % self.name
        util.makedirs(path)
        with open('%s/%d.json' % (path, global_step), 'w') as f:
          f.write(ctf)
        #self.writer.add_run_metadata(run_metadata, 'step %d' % global_step, global_step)
    
    return outputs

  # so it can serialize itself to send to actors 
  def blob(self):
    with self.graph.as_default():
      values = self.sess.run(self.variables)
      return {var.name: val for var, val in zip(self.variables, values)}