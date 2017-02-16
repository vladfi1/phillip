# copy this file to ~/.sopel/modules/
# you will have to set up ~/.sopel/default.cfg to log in automatically as your bot
# then run sopel

from sopel import module
import os, signal, subprocess
from phillip import run
from twitch import key

current_thread = None
stream_thread=None

stream_args = [
  'ffmpeg',
  '-video_size', '1920x1080',
  '-framerate', '30',
  '-f', 'x11grab', '-i', ':0.0',
  '-c:v', 'libx264', '-preset', 'veryfast',
  '-maxrate', '3000k', '-bufsize', '6000k',
  '-pix_fmt', 'yuv420p',  '-g', '50',
  '-f', 'flv',
  'rtmp://live.twitch.tv/app/' + key
]

@module.commands('echo', 'repeat')
def echo(bot, trigger):
    bot.reply(trigger.group(2))

@module.commands('helloworld')
def helloworld(bot, trigger):
    bot.say('Hello, world!')

@module.commands('dolphin')
def dolphin(bot, trigger):
    bot.say("5.0-2538")

@module.thread(False)
@module.commands('play')
def play(bot, trigger):
  global current_thread, stream_thread
  
  if current_thread:
    bot.say("already playing, sorry")
    return
  
  code = trigger.group(2)
  
  args = dict(
    load="/home/vlad/Repos/phillip/agents/FalconFalconBF/",
    gui=True,
    zmq=0,
    exe='dolphin-emu',
    iso="/home/vlad/ISO/SSBM.iso",
    netplay=code,
    start=0,
    fullscreen=True,
  )
  
  #current_thread = Process(target=run.run, kwargs=args)
  #current_thread.start()
  #return
  
  cmd = ["phillip"]
  for k, v in args.items():
    if type(v) is bool and v:
      cmd.append('--' + k)
    else:
      cmd.append('--' + k)
      cmd.append(str(v))
  
  print(cmd)
  
  current_thread = subprocess.Popen(cmd, start_new_session=True)
  #current_thread = subprocess.Popen(['echo', 'fasd'])
  
  stream_thread = subprocess.Popen(stream_args, start_new_session=True)

@module.thread(False)
@module.commands('stop')
def stop(bot, trigger):
  #bot.say('stop?')
  global current_thread, stream_thread
  
  #import ipdb; ipdb.set_trace()
  if current_thread:
    #current_thread.terminate()
    os.killpg(os.getpgid(current_thread.pid), signal.SIGTERM)
    current_thread = None
    
    os.killpg(os.getpgid(stream_thread.pid), signal.SIGTERM)
    stream_thread = None
  else:
    bot.say("nothing running")

