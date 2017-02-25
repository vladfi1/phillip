#The Phillip AI
An SSBM player based on deep reinforcement learning.

##Rough Setup Steps:

Tested on: Ubuntu >=14.04, OSX

### Requirements

1. A recent version of Dolphin.
2. Python 3.
3. [TensorFlow 0.11](https://www.tensorflow.org/versions/r0.11/get_started/os_setup).
4. A few Python packages

    pip3 install attrs

5. Install Phillip:

    pip3 install -e .

### Play

Trained agents are stored in the `agents` directory.

    phillip --gui --human --start 0 --load agents/FalconFalconFD

### Train

Training is controlled by `train.py`. See also `runner.py` and `launcher.py` for training massively in parallel on Slurm clusters. Phillip has been trained at the [MGHPCC](http://www.mghpcc.org/).

## Recordings

I've been streaming practice play over at http://twitch.tv/x_pilot. There are also some recordings on my [YouTube channel](https://www.youtube.com/channel/UCzpDWSOtWpDaNPC91dqmPQg).

##Credits

Big thanks to https://github.com/altf4/SmashBot for getting me started, and to https://github.com/spxtr/p3 for a Python memory watcher. Some code for Dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure Python).
