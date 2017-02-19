#The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

##Rough Setup Steps:

Tested on: Ubuntu >=14.04, OSX

### Requirements

1. A recent version of dolphin.
2. Python 3.
3. Tensorflow - https://www.tensorflow.org/versions/r0.9/get_started/os_setup.html#download-and-setup
4. A few python packages - `pip3 install attrs`
5. Install phillip:

    pip3 install -e .

### Play

Trained agents are stored in the `agents` directory.

    phillip --gui --human --start 0 --load agents/FalconFalconFD

### Train

Training is controlled by `train.py`. See also `runner.py` and `launcher.py` for training massively in parallel on slurm clusters. Phillip has been trained at the [MGHPCC](http://www.mghpcc.org/).

## Recordings

I've been streaming practice play over at http://twitch.tv/x_pilot. There are also some recordings on my [youtube channel](https://www.youtube.com/channel/UCzpDWSOtWpDaNPC91dqmPQg).

##Credits

Big thanks to https://github.com/altf4/SmashBot for getting me started, and to https://github.com/spxtr/p3 for a python memory watcher. Some code for dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure python).
