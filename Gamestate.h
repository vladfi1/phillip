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
	FSMASH_MID = 0x3c,
	SHIELD = 0xb3,
};

#endif
