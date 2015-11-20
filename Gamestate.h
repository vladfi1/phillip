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
	uint player_one_character;
	bool player_one_invulnerable;
	uint player_one_hitlag_frames_left;
	uint player_one_hitstun_frames_left;
	uint player_one_jumps_left;
	bool player_one_charging_smash;
	bool player_one_on_ground;
	float player_one_speed_air_x_self;
	float player_one_speed_y_self;
	float player_one_speed_x_attack;
	float player_one_speed_y_attack;
	float player_one_speed_ground_x_self;

	uint player_two_percent;
	uint player_two_stock;
	//True is right, false is left
	bool player_two_facing;
	float player_two_x;
	float player_two_y;
	uint player_two_action;
	uint player_two_character;
	bool player_two_invulnerable;
	uint player_two_hitlag_frames_left;
	uint player_two_hitstun_frames_left;
	uint player_two_jumps_left;
	bool player_two_charging_smash;
	bool player_two_on_ground;
	float player_two_speed_air_x_self;
	float player_two_speed_y_self;
	float player_two_speed_x_attack;
	float player_two_speed_y_attack;
	float player_two_speed_ground_x_self;

	//Character select screen pointer for player 2
	float player_two_pointer_x;
	float player_two_pointer_y;

	uint frame;
	uint menu_state;
};

enum ACTION
{
	STANDING = 0x0e,
	WALK_SLOW = 0x0f,
	WALK_MIDDLE = 0x10,
	WALK_FAST = 0x11,
	DASHING = 0x14,
	RUNNING = 0x15,
	KNEE_BEND = 0x18, //pre-jump animation.
	CROUCHING = 0x28,
	LANDING = 0x2a, //Can be canceled. Not stunned
	FSMASH_MID = 0x3c,
	SHIELD = 0xb3,
	GRAB = 0xd4,
	GRAB_RUNNING = 0xd6,
	EDGE_TEETERING = 0xF6,
	EDGE_CATCHING = 0xFC, //Initial grabbing of edge, stuck in stun here
	EDGE_HANGING = 0xFD,
	EGDE_ROLL_SLOW = 0x102, // >= 100% damage
	EDGE_ROLL_QUICK = 0x103, // < 100% damage
	UP_B = 0x170,	//The upswing of the UP-B
	MARTH_COUNTER = 0x171,
	MARTH_COUNTER_FALLING = 0x173,

};

enum MENU
{
	CHARACTER_SELECT = 33685760,
	STAGE_SELECT = 33685761,
	IN_GAME = 33685762,
};

enum CHARACTER
{
	FOX = 0x0a,
	MEWTWO = 0x15,
	MARTH = 0x17,
};

#endif
