# copy/symlink this file to ~/.sopel/modules/

# you will have to set up ~/.sopel/default.cfg to log in automatically as your bot
# here is my defult.cfg:

sample_cfg = """
[core]
nick = x_pilot_bot
host = irc.chat.twitch.tv
use_ssl = false
port = 6667
auth_method = server
auth_password = <bot oauth token>
owner = x_pilot_bot
channels = #x_pilot
prefix = !
"""
# get the oauth token from https://twitchapps.com/tmi/
# this should be the token for your bot account, if you made one

# now run sopel from the command line

from sopel import module
import os, signal, subprocess
#from phillip import run

# key should be your twitch stream key (https://www.twitch.tv/broadcast/dashboard/streamkey)
# this is for your regular account, not the bot
# I made a file globals.py on my PYTHONPATH for things like this
from globals import twitch_key, dolphin_iso_path

# should point to FM 4.4
# linux install guide: https://github.com/Ptomerty/FasterMelee-installer
dolphin_path = 'launch-faster-melee'

agent_path = '/home/vlad/Repos/phillip/agents/'
agent = 'FalconFalconBF'

current_thread = None
stream_thread = None

stream = False

stream_args = [
  'ffmpeg',
  '-video_size', '1366x768',
  '-framerate', '30',
  '-f', 'x11grab', '-i', ':0.0',
  '-c:v', 'libx264', '-preset', 'veryfast',
  '-maxrate', '3000k', '-bufsize', '6000k',
  '-pix_fmt', 'yuv420p',  '-g', '50',
  '-f', 'flv',
  'rtmp://live.twitch.tv/app/' + twitch_key
]

@module.commands('echo', 'repeat')
def echo(bot, trigger):
    bot.reply(trigger.group(2))

@module.commands('helloworld')
def helloworld(bot, trigger):
    bot.say('Hello, world!')

@module.commands('dolphin')
def dolphin(bot, trigger):
    bot.say("Faster Melee 4.4")

instructions = """
1. Install dolphin 5.0-2538
2. Use the smashladder configuration (no memory card, cheats on, netplay community settings Gecko code)
3. host a netplay lobby (traversal server)
4. Go to twitch.tv/x_pilot

commands:

!play <code> - the bot will join your netplay lobby
!stop - stops the bot so others can play
!agents - list available agents to play against
!agent <agent> - set the agent

Bot is in norcal.
"""

@module.commands('instructions', 'rules')
def instructions(bot, trigger):
    bot.say(instructions)

@module.commands('agent')
def set_agent(bot, trigger):
    global agent_path, agent
    
    new_agent = trigger.group(2)
    path = agent_path + new_agent
    
    if not os.path.exists(path):
      bot.say('Invalid agent!')
      return
    
    agent = new_agent

@module.commands('agents')
def agents(bot, trigger):
    bot.say(' '.join(os.listdir(agent_path)))

@module.thread(False)
@module.commands('play')
def play(bot, trigger):
  global current_thread, stream_thread
  
  if current_thread:
    bot.say("already playing, sorry")
    return
  
  code = trigger.group(2)
  
  args = dict(
    load=agent_path + agent,
    gui=True,
    zmq=0,
    exe=dolphin_path,
    fm = True,
    iso_path=dolphin_iso_path,
    netplay=code,
    start=0,
    fullscreen=True,
    delay=0,
    act_every=1,
    reload=60,
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
  if stream:
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
    
    if stream:
      os.killpg(os.getpgid(stream_thread.pid), signal.SIGTERM)
      stream_thread = None
  else:
    bot.say("nothing running")

@module.commands('kill')
def kill(bot, trigger):
  import os
  os.system('killall ' + dolphin_path)

