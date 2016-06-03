import binascii
import zmq
import util

def parseMessage(message):
  lines = message.splitlines()
  
  diffs = util.chunk(lines, 2)
  
  for diff in diffs:
    diff[1] = binascii.unhexlify(diff[1].zfill(8))
  
  return diffs

class MemoryWatcher:
  def __init__(self, path):
    context = zmq.Context()

    self.socket = context.socket(zmq.REP)
    self.socket.bind("ipc://" + path)
    
    self.messages = None
  
  def get_messages(self):
    if self.messages is None:
      message = self.socket.recv()
      message = message.decode('utf-8')
      self.messages = parseMessage(message)
    
    return self.messages
  
  def advance(self):
    self.socket.send(b'')
    self.messages = None
