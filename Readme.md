# The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

## Requirements

Tested on: Ubuntu >=14.04, OSX, Windows 7/8/10.

1. The dolphin emulator. Probably need to compile from source on Linux. On Windows you'll need to install a [custom dolphin version](https://github.com/vladfi1/dolphin/releases/tag/v5.1-alpha) - just unpack the zip somewhere.
2. The SSBM iso image. Must be NTSC 1.02.
3. Python 3.
4. Install phillip. This should pull in python dependencies like tensorflow.

    pip3 install -e .

## Play

You will need to know where dolphin is located. On Mac the dolphin path will be `~/../../Applications/Dolphin.app/Contents/MacOS/Dolphin`. On Windows it will be the path to the `.exe` you unzipped.

    python3 phillip/run.py --gui --human --start 0 --load agents/FalconFalconBF --iso path/to/SSBM.iso --exe path/to/dolphin

Trained agents are stored in the `agents` directory. Aside from `FalconFalconBF`, the agents in `agents/delay0/` are also fairly strong. Run with `--help` to see all options.

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

## Credits

Big thanks to https://github.com/altf4/SmashBot for getting me started, and to https://github.com/spxtr/p3 for a python memory watcher. Some code for dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure python).
