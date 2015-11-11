#ifndef GAMESTATE_H
#define GAMESTATE_H

struct GameState
{
	uint player_one_percent;
	uint player_one_stock;
	//True is right, false is left
	bool player_one_facing;
	float player_one_x;
	float player_one_y;
	uint player_one_action;

	uint player_two_percent;
	uint player_two_stock;
	//True is right, false is left
	bool player_two_facing;
	float player_two_x;
	float player_two_y;
	uint player_two_action;

	uint frame;
};

enum ACTION
{
	STANDING = 0x0e,
	WALK_SLOW = 0x0f,
	WALK_MIDDLE = 0x10,
	WALK_FAST = 0x11,
	KNEE_BEND = 0x18, //pre-jump animation.
	CROUCHING = 0x28,
	LANDING = 0x2a, //Can be canceled. Not stunned
	FSMASH_MID = 0x3c,
	SHIELD = 0xb3,
	GRAB = 0xd4,
	GRAB_RUNNING = 0xd6,
};

#endif
