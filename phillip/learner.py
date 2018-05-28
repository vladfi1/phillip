from phillip import RL

class Learner(RL.RL):
  def __init__(self, debug=False, **kwargs):
    super(Learner, self).__init__(mode=RL.Mode.LEARNER, debug=debug, **kwargs)