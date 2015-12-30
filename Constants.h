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

//The depth of Marth at which he can't recover onto the stage anymore. If he's gone down this low, he's dead
#define MARTH_ONE_JUMP_EVENT_HORIZON -96
#define MARTH_NO_JUMP_EVENT_HORIZON -74

//The depth where Marth has to UP-B to recover, jumping alone isn't enough
#define MARTH_JUMP_ONLY_EVENT_HORIZON -47

#define FOX_SHINE_RADIUS 11.80
#define FOX_ROLL_BACK_DISTANCE 33.6
#define FOX_ROLL_FRAMES 35

//This is a little conservative, actually
#define FOX_UPSMASH_RANGE 17.5
//The closest hitbox. The one that comes out on frame 7
#define FOX_UPSMASH_RANGE_NEAR 12.5

#endif
