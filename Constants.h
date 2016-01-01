#ifndef CONSTANTS_H
#define CONSTANTS_H

//TODO: maybe marth specific
#define EDGE_HANGING_Y_POSITION -23.7163639069

//Max tipper range, measured from Marth's center
#define MARTH_FSMASH_RANGE 38.50
#define MARTH_ROLL_DISTANCE 40.2
#define MARTH_EDGE_ROLL_DISTANCE 41.52
#define MARTH_GETUP_DISTANCE 11.33

#define MARTH_ROLL_FRAMES 35
#define MARTH_EDGE_ROLL_FRAMES 48
#define MARTH_EDGE_ROLL_SLOW_FRAMES 98
#define MARTH_EDGE_GETUP_QUICK_FRAMES 32
#define MARTH_EDGE_GETUP_SLOW_FRAMES 58

#define MARTH_UP_B_HEIGHT 48
#define MARTH_UP_B_X_DISTANCE 18

#define MARTH_RUN_SPEED 1.7775000334
#define MARTH_DOUBLE_JUMP_HEIGHT 23

//The depth of Marth at which he can't recover anymore. If he's gone down this low, he's dead
#define MARTH_LOWER_EVENT_HORIZON -96

//The depth where Marth has to UP-B to recover, jumping and/or air dodging alone isn't enough
#define MARTH_JUMP_ONLY_EVENT_HORIZON -47

//The depth where Marth cannot land on the stage anymore. He has to grab the edge
#define MARTH_RECOVER_HIGH_EVENT_HORIZON -81

#define MARTH_UPSMASH_KILL_PERCENT 79

#define FOX_SHINE_RADIUS 11.80
#define FOX_ROLL_BACK_DISTANCE 33.6
#define FOX_ROLL_FRAMES 35

//This is a little conservative, actually
#define FOX_UPSMASH_RANGE 17.5
//The closest hitbox. The one that comes out on frame 7
#define FOX_UPSMASH_RANGE_NEAR 12.5

#endif
