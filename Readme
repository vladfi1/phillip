Works on: Ubuntu 15.04 (Maybe others, but that's all I've tested)

Really Rough Build Steps:

1) Get a working build of dolphin from source. The latest maaster branch should be fine.
2) Apply the patch included along with the cpu source code: dolphin-memstate.patch
3) Create a named pipe: ~/.dolphin/Pipes/cpu-level-11

```
mkfifo ~/.dolphin/Pipes/cpu-level-11
```

4) Configure your controller settings for P1 and P2. The CPU will take player 2.
5) Run dolphin and Melee.
6) Set player 1 to Marth and player 2 to Fox, stage to Final Destination. Start the match.
7) Run ./cpu

```
./cpu
```

8) Move focus over to the dolphin window. (Or else turn on background input on the controller)
