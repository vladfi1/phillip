#The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

## Requirements

Tested on: Ubuntu >=14.04, OSX. If you want Windows support, go [bug](https://bugs.dolphin-emu.org/issues/10126) the dolphin developers to support MemoryWatcher and Pipe Input on Windows! A fork that supports this is under works.

1. A recent version of dolphin. Probably need to compile from source on Linux.
2. Python 3.
3. [Tensorflow 0.11](https://www.tensorflow.org/versions/r0.11/get_started/os_setup).
4. A few python packages

    pip3 install attrs

5. Install phillip:

    pip3 install -e .

## Play

Trained agents are stored in the `agents` directory.

    phillip --gui --human --start 0 --load agents/FalconFalconFD

## Train

Training is controlled by `phillip/train.py`. See also `runner.py` and `launcher.py` for training massively in parallel on slurm clusters. Phillip has been trained at the [MGHPCC](http://www.mghpcc.org/). It is recommended to train with a custom dolphin from `https://github.com/vladfi1/dolphin` - the below commands will likely fail otherwise.

Local training is also possible. First, edit `runner.py` with your desired training params (advanced). Then do:

    python3 runner.py # will output a path
    python3 launcher.py saves/path/ --init --local [--agents number_of_agents] [--log_agents]

To view stats during training:

    tensorboard --logdir logs/

The trainer and (optionally) agents redirect their stdout/err to `slurm_logs/`. To end training:

    kill $(cat saves/path/pids)

To resume training run `launcher.py` again, but omit the `--init` (it will overwrite your old network).

## Support

Come to the [Discord](https://discord.gg/KQ8vhd6)!

## Recordings

I've been streaming practice play over at http://twitch.tv/x_pilot. There are also some recordings on my [youtube channel](https://www.youtube.com/channel/UCzpDWSOtWpDaNPC91dqmPQg).

##Credits

Big thanks to https://github.com/altf4/SmashBot for getting me started, and to https://github.com/spxtr/p3 for a python memory watcher. Some code for dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure python).
