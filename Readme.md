#Level 11 CPU
*(We skipped ten and cranked it straight up to eleven)*

##Really Rough Setup Steps:

###Works on: Ubuntu 15.04 (Maybe others, but that's all I've tested)

1. Get a working build of dolphin from source. The latest master branch should be fine. You can find it here:
https://github.com/dolphin-emu/dolphin
2. Apply the patch included along with the cpu source code: `dolphin-memstate.patch`
```
cp dolphin-memstate.patch [dolphin-directory]
cd [dolphin-directory]
patch -p1 dolphin-memstate.patch
```
3. Create a named pipe for our CPU to talk over. This is how the CPU presses buttons programmatically over a virtual controller.
```
mkfifo ~/.dolphin/Pipes/cpu-level-11
```
4. Configure your controller settings for player 1 and player 2. The CPU will take player 2. You'll probably want a GameCube controller adapter. But configuring that is out of the scope of this document.
5. Run dolphin and start up Melee.
6. Run `./cpu`
```
./cpu
```
8. Move focus over to the dolphin window. (Or else turn on background input on the controller) Just click on the dolphin window to do this.
7. Set player 1 to Marth. The CPU will choose its own character.  Set the stage to Final Destination. Start the match.
