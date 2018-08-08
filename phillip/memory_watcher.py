import binascii
from . import util
import os
import sys
import socket

def parseMessage(message):
  lines = message.splitlines()
  
  assert(len(lines) % 2 == 0)

  diffs = util.chunk(lines, 2)
  
  for diff in diffs:
    diff[1] = binascii.unhexlify(diff[1].zfill(8))
  
  return diffs

class MemoryWatcherZMQ:
  def __init__(self, path=None, port=None, pull=False):
    try:
      import zmq
    except ImportError as err:
      print("ImportError: {0}".format(err))
      sys.exit("Need zmq installed.")

    self.pull = pull or port
    context = zmq.Context()
    self.socket = context.socket(zmq.PULL if self.pull else zmq.REP)
    if path:
      self.socket.bind("ipc://" + path)
    elif port:
      self.socket.bind("tcp://127.0.0.1:%d" % port)
    else:
      raise Exception("Must specify path or port.")
    
    self.messages = None
  
  def get_messages(self):
    if self.messages is None:
      message = self.socket.recv()
      message = message.decode('utf-8')
      self.messages = parseMessage(message)
    
    return self.messages
  
  def advance(self):
    if not self.pull:
      self.socket.send(b'')
    self.messages = None

class MemoryWatcher:
  """Reads and parses game memory changes.

  Pass the location of the socket to the constructor, then either manually
  call next() on this class to get a single change, or else use it like a
  normal iterator.
  """
  def __init__(self, path):
    """Creates the socket if it does not exist, and then opens it."""
    try:
      os.unlink(path)
    except OSError:
      pass
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    self.sock.settimeout(1)
    self.sock.bind(path)

  def __del__(self):
    """Closes the socket."""
    self.sock.close()
  
  def get_messages(self):
    try:
      data = self.sock.recv(1024).decode('utf-8')
      data = data.strip('\x00')
    except socket.timeout:
      return []
    
    return parseMessage(data)
    
  def advance(self):
    pass

