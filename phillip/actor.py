from phillip import RL

# class Mode(Enum):
#   LEARNER = 0
#   ACTOR = 1

class Actor(RL.RL):
  def __init__(self, debug=False, **kwargs):
    super(Actor, self).__init__(mode=RL.Mode.ACTOR, debug=debug, **kwargs)