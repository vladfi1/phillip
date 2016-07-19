#The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

##Rough Setup Steps:

Tested on: Ubuntu >=14.04, OSX

### Requirements

1. A recent version of dolphin.
2. Python 3.
3. Tensorflow - https://www.tensorflow.org/versions/r0.9/get_started/os_setup.html#download-and-setup
4. A few python packages - `pip3 install attrs`

### Play

1. Configure your controller settings for player 1 and player 2. You will play as Player 1, Phillip will take Player 2. You'll probably want a GameCube controller adapter. Configuring controller settings is out of the scope of this document, but check out the file `GCPadNew.ini` provided here for an example controller config that ought to work. Just stick that in your Dolphin config directory.
2. A saved model. A bot trained in Falcon dittos on battlefield is available. Unfortunately some updates to the learning algorithm break compatibility with old saves.
3. The `run.py` script can do pretty much everything. Pass `--help` to see the full list of options. An example execution would be:

    python3 run.py --model ActorCriticSplit --act_every 3 --path path/to/saved/model/dir/ --nodump --gui --nosetup --nozmq --dolphin_dir path/to/dolphin/user/dir/

### Train

Training is controlled by `train.py`. See also `runner.py` for training massively in parallel on slurm clusters. Phillip has been trained at the [MGHPCC](http://www.mghpcc.org/).

## Recordings

I've been streaming practice play over at twitch.tv/xpilot. There you can find lots of recordings of the bot's evolution over time.

##Credits

Big thanks to https://github.com/altf4/SmashBot for getting me started, and to https://github.com/spxtr/p3 for a python memory watcher. Some code for dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure python).
