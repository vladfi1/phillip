class Default:
  options = []
  
  def __init__(self, **kwargs):
    for name, default in self.options:
      value = None
      if name in kwargs:
        value = kwargs[name]
      if value is None:
        value = default
      setattr(self, name, value)
  
  def items(self):
    for name, _ in self.options:
      yield name, getattr(self, name)
  
  def label(self):
    label = self.__class__.__name__
    for item in self.items():
      label += "_%s_%s" % item
    return label
  
  def __repr__(self):
    fields = ", ".join(["%s=%s" % (name, getattr(self, name)) for name, _ in self.options])
    return "%s(%s)" % (self.__class__.__name__, fields)
