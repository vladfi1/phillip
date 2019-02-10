import pickle

class Default:
  _options = []
  
  _members = []
  
  def __init__(self, init_members=True, **kwargs):
    self._kwargs = kwargs
    
    for opt in self._options:
      value = None
      if opt.name in kwargs:
        value = kwargs[opt.name]
      if value is None:
        value = opt.default
      setattr(self, opt.name, value)
    
    if init_members:
      self._init_members(**kwargs)
  
  def _init_members(self, **kwargs):
    for name, cls in self._members:
      setattr(self, name, cls(**kwargs))
  
  def items(self):
    for opt in self._options:
      yield opt.name, getattr(self, opt.name)
    for name, _ in self._members:
      yield name, getattr(self, name)
  
  def label(self):
    label = self.__class__.__name__
    for item in self.items():
      label += "_%s_%s" % item
    return label
  
  def __repr__(self):
    fields = ", ".join("%s=%s" % (name, str(value)) for name, value in self.items())
    return "%s(%s)" % (self.__class__.__name__, fields)
  
  @classmethod
  def full_opts(cls):
    yield from cls._options
    for _, cls_ in cls._members:
      yield from cls_.full_opts()
  
  def __getstate__(self):
    return self._kwargs
  def __setstate__(self, d):
    self.__init__(**d)
  
  def dump(self, f):
    pickle.dump(self._kwargs, f)
  
  @classmethod
  def load(cls, f, **override):
    kwargs = pickle.load(f)
    kwargs.update(**override)
    return cls(**kwargs)
  
  @classmethod
  def update_parser(self, parser):
    for option in self.full_opts():
      option.update_parser(parser)
  
class Option:
  def __init__(self, name, _skip=False, **kwargs):
    self.name = name
    self._skip = _skip
    self.default = None
    self.__dict__.update(kwargs)
    self.kwargs = kwargs.copy()
    
    # don't pass default on to argparse
    self.kwargs['default'] = None
  
  def update_parser(self, parser):
    if self._skip:
      return
    
    flag = "--" + self.name
    if flag in parser._option_string_actions:
      print("warning: already have option %s. skipping"%self.name)
      pass
    else:
      parser.add_argument(flag, **self.kwargs)

