from phillip import RL

class Actor(RL.RL):
  def __init__(self, debug=False, **kwargs):
    super(Actor, self).__init__(mode=RL.Mode.ACTOR, debug=debug, **kwargs)

  def act(self, input_dict, verbose=False):
    feed_dict = dict(util.deepValues(util.deepZip(self.input, input_dict)))
    policy, hidden = self.sess.run(self.run_policy, feed_dict)
    return self.policy.act(policy, verbose), hidden

  # for unserializing updated weights sent from learners. 
  def unblob(self, blob):
    #self.sess.run(self.unblobber, {self.placeholders[k]: v for k, v in blob.items()})
    self.sess.run(self.unblobber, {v: blob[k] for k, v in self.placeholders.items()})