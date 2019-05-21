# The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

## Requirements

Tested on: Ubuntu >=14.04, OSX, Windows 7/8/10.

1. The dolphin emulator. You will probably need to compile from source on Linux. On Windows you'll need to install a [custom dolphin version](https://github.com/vladfi1/dolphin/releases/download/v5.2-alpha/win-mw-push.zip) - just unpack the zip somewhere.
2. The SSBM iso image. Tested with NTSC 1.02, but other versions will probably work too.
3. Python 3. On Windows, you can use [Anaconda](https://repo.continuum.io/archive/Anaconda3-4.4.0-Windows-x86_64.exe) which sets up the necessary paths. You can also use the linux subsytem on Windows 10.
4. `pip3 install tensorflow`, or `tensorflow-gpu` if you plan on training with an nvidia gpu. Phillip doesn't depend on tensorflow so that you can choose which one you want to use.
5. Install [phillip](https://github.com/vladfi1/phillip/archive/master.zip).

```bash
cd path/to/phillip # future commands should be run from here
pip3 install -e . # "." is the path to the current directory - don't omit!
```

Installing in editable mode (`-e`) allows you to make local changes without reinstalling, which is useful if you are using a cloned repo and want to update by pulling (`git pull`).

If cloning, you may wish to use `--depth 1` to avoid downloading large files from phillip's history (most of which are now gone and should be purged from git). These are the saved agents, which are in the process of being moved to [git large file storage](https://git-lfs.github.com/). Currently the best agents such as `agents/delay18/FalcoBF` live there. To get it:

```bash
sudo apt-get install git-lfs # on ubuntu; for other systems see the website
git-lfs install
git-lfs pull
```

As an alternative, you can download a [zip](https://drive.google.com/open?id=1uHghos9e3aXoT19Tn9v6rDYBBclCWt-U) with all the agents.

## Play

You will need to know where dolphin is located. On Mac the dolphin path will be `~/../../Applications/Dolphin.app/Contents/MacOS/Dolphin`. If `dolphin-emu` is already on your `PATH` then you can omit this.

    python3 phillip/run.py --gui --human --start 0 --reload 0 --epsilon 0 --load agents/FalconFalconBF --iso /path/to/SSBM.iso --exe /path/to/dolphin [--windows]

Trained agents are stored in the `agents` directory. Aside from `FalconFalconBF`, the agents in `agents/delay0/` are also fairly strong. Run with `--help` to see all options.

### Windows Notes

- The `--exe` will be the path to the `Binary\x64\Dolphin.exe` you unzipped. In general, the forward `/`s should be back `\`s for all paths, unless you are using MinGW, Cygwin, git bash, or some other unix shell emulator.
- You may need to omit the `3` from commands like `python3` and `pip3`.
- If not using Anaconda, you will likely need to modify your PATH so that python is visible to the command prompt.
- Communication with dolphin is done over the local loopback interface, enabled with the `--tcp 1` flag (now implied by `--windows`). You may also need to open port 5555 in your firewall.
- If on Windows 10 you can do everything in the Linux subsystem and follow the linux instructions, except for obtaining dolphin. You will need to pass in an explicit user directory with `--user tmp` (the temp directories that python creates start with `/tmp/...` and aren't valid for windows dolphin).

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

Thanks to [microsoftv](https://github.com/microsoftv) there is now an [instructional video](https://www.youtube.com/watch?v=hxzpK719wV4) as well!

## Support

Come to the [Discord](https://discord.gg/KQ8vhd6)!

## Recordings

I've been streaming practice play over at http://twitch.tv/x_pilot. There are also some recordings on my [youtube channel](https://www.youtube.com/channel/UCzpDWSOtWpDaNPC91dqmPQg).

## Credits

Big thanks to [altf4](https://github.com/altf4/SmashBot) for getting me started, and to [spxtr](https://github.com/spxtr/p3) for a python memory watcher. Some code for dolphin interaction has been borrowed from both projects (mostly the latter now that I've switched to pure python).

