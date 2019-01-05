from bottle import Bottle, run, template, request
import subprocess
import time

app = Bottle()

def validate(code):
  return len(code) == 8 and code.isalnum()

start_times = []

def cull_times():
  global start_times

  current = time.time()

  # remove anything more than 20 min old
  start_times = [t for t in start_times if current - t < 1200]

  return len(start_times)


MAX_GAMES = 10

def play(code, delay=6, real_delay=0):
  if not validate(code):
    return request_match_page() + template('Invalid code <b>{{code}}</b>', code=code)

  if cull_times() >= MAX_GAMES:
    return request_match_page() + template('Sorry, too many games running')


  command = 'sbatch -t 20:00 -c 2 --mem 1G -x node[001-030]' # --qos tenenbaum'
  command += ' --output slurm_logs/server/%s.out' % code
  command += ' --error slurm_logs/server/%s.err' % code
  command += ' netplay.sh %s %s %s' % (code, delay, real_delay)
  print(command)
  try:
    subprocess.run(command.split())
  except:
    return request_match_page() + template('Unknown error occurred. Make sure your netplay code <b>{{code}}</b> is valid.', code=code)

  start_times.append(time.time())
  return request_match_page() + template('Phillip netplay started with code <b>{{code}}</b>!', code=code)

@app.get('/')
def request_match_page():
  return '''
    <form action="/request_match" method="post">
      Code: <input name="code" type="text" /> Your netplay host code. <br/>
      Reaction Time (x50ms): <input name="delay" type="number" value="6"/> Higher => phillip plays worse. <br/>
      Netplay Lag (x50ms): <input name="real_delay" type="number" value="0" /> If unsure, leave at 0. <br/>
      <input value="Request match" type="submit" /> <br/>
      Please report issues in the <a href="https://discord.gg/KQ8vhd6">Discord Support Channel</a> <br/>
    </form>
  '''

@app.post('/request_match')
def request_match():
  args = ['code', 'delay', 'real_delay']
  return play(**{k: request.forms.get(k) for k in args})
    
run(app, host='0.0.0.0', port=8484)
