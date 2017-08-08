# The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

## Requirements

Tested on: Ubuntu >=14.04, OSX, Windows 7/8/10.

1. The dolphin emulator. You will probably need to compile from source on Linux. On Windows you'll need to install a [custom dolphin version](https://github.com/vladfi1/dolphin/releases/tag/v5.1-alpha) - just unpack the zip somewhere.
2. The SSBM iso image. Must be NTSC 1.02. Mods like netplay community builds and 20XX may also work, but automatic character and stage selection may not work properly (you can still do it manually).
3. Python 3. On Windows, you can use [Anaconda](https://repo.continuum.io/archive/Anaconda3-4.4.0-Windows-x86_64.exe) which sets up the necessary paths.
4. Install [phillip](https://github.com/vladfi1/phillip/archive/master.zip). This will pull in python dependencies like tensorflow.

```bash
cd path/to/phillip # future commands should be run from here
pip3 install [-e] .
```

Installing in editable mode (`-e`) allows you to make local changes without reinstalling, which is useful if you are using a cloned repo and want to update by pulling. If cloning, you may wish to use `--depth 1` to avoid downloading large files from phillip's history (most of which are now gone and should be purged from git).

## Play

You will need to know where dolphin is located. On Mac the dolphin path will be `~/../../Applications/Dolphin.app/Contents/MacOS/Dolphin`. If `dolphin-emu` is already on your `PATH` then you can omit this.

    python3 phillip/run.py --gui --human --start 0 --reload 0 --epsilon 0 --load agents/FalconFalconBF --iso path/to/SSBM.iso --exe path/to/dolphin [--tcp 1]

Trained agents are stored in the `agents` directory. Aside from `FalconFalconBF`, the agents in `agents/delay0/` are also fairly strong. Run with `--help` to see all options.

### Windows Notes

- The `--exe` will be the path to the `Binary\x64\Dolphin.exe` you unzipped. In general, the forward `/`s should be back `\`s for all paths, unless you are using MinGW, Cygwin, git bash, or some other unix shell emulator.
- You may need to omit the `3` from commands like `python3` and `pip3`.
- If not using Anaconda, you will likely need to modify your PATH so that python is visible to the command prompt.
- Because communication with dolphin is done over the local loopback interface, you will need to add the `--tcp 1` flag. You may also need to open port 5555 in your firewall.

## Train

Training is controlled by `phillip/train.py`. See also `runner.py` and `launcher.py` for training massively in parallel on slurm clusters. Phillip has been trained at the [MGHPCC](http://www.mghpcc.org/). It is recommended to train with a [custom dolphin](https://github.com/vladfi1/dolphin) which uses zmq to synchronize with the AI - the below commands will likely fail otherwise.

Local training is also possible. First, edit `runner.py` with your desired training params (advanced). Then do:

    python3 runner.py # will output a path
    python3 launcher.py saves/path/ --init --local [--agents number_of_agents] [--log_agents]

To view stats during training:

    tensorboard --logdir logs/

The trainer and (optionally) agents redirect their stdout/err to `slurm_logs/`. To end training:

    kill $(cat saves/path/pids)

To resume training run `launcher.py` again, but omit the `--init` (it will overwrite your old network).

Training on Windows is not supported.

## Support

Come to the [Discord](https://discord.gg/KQ8vhd6)!

## Recordings

I've been streaming practice play over at http://twitch.tv/x_pilot. There are also some recordings on my [youtube channel](https://www.youtube.com/channel/UCzpDWSOtWpDaNPC91dqmPQg).

## Credits

Big thanks to [altf4](https://github.com/altf4/SmashBot) for getting me started, and to [spxtr](https://github.com/spxtr/p3) for a python memory watcher. Some code for dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure python).

