from globals import twitch_key

stream_args = [
  'ffmpeg',
  '-video_size', '1366x768',
  '-framerate', '30',
  '-f', 'x11grab', '-i', ':0.0',
  '-f', 'pulse', '-ac', '2', '-i', 'default',
  '-c:v', 'libx264', '-preset', 'veryfast',
  '-maxrate', '3000k', '-bufsize', '6000k',
  '-pix_fmt', 'yuv420p',  '-g', '50',
  '-c:a', 'mp3', '-b:a', '160k', '-ar', '44100', '-threads', '0', '-strict', '-2',
  '-f', 'flv',
  'rtmp://live.twitch.tv/app/' + twitch_key
  #'test.flv'
]

import subprocess
import os

#proc = subprocess.Popen(stream_args)
os.system(' '.join(stream_args))

