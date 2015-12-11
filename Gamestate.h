#ifndef GAMESTATE_H
#define GAMESTATE_H

#include <sys/types.h>

struct GameState
{
	uint player_one_percent;
	uint player_one_stock;
	//True is right, false is left
	bool player_one_facing;
	float player_one_x;
	float player_one_y;
	uint player_one_action;
	uint player_one_action_counter;
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
	uint player_two_action_counter;
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
	TURNING = 0x12,
	TURNING_RUN = 0x13,
	DASHING = 0x14,
	RUNNING = 0x15,
	KNEE_BEND = 0x18, //pre-jump animation.
	JUMPING_FORWARD = 0x19,
	JUMPING_BACKWARD = 0x1A,
	JUMPING_ARIAL_FORWARD = 0x1b,
	JUMPING_ARIAL_BACKWARD = 0x1c,
	FALLING = 0x1D,	//The "wait" state of the air.
	CROUCHING = 0x28,
	LANDING = 0x2a, //Can be canceled. Not stunned
	LANDING_SPECIAL = 0x2b, //Landing special, like from wavedash. Stunned.
	NEUTRAL_ATTACK_1 = 0x2c,
	NEUTRAL_ATTACK_2 = 0x2d,
	NEUTRAL_ATTACK_3 = 0x2e,
	DASH_ATTACK = 0x32,
	FTILT_HIGH = 0x33,
	FTILT_HIGH_MID = 0x34,
	FTILT_MID = 0x35,
	FTILT_LOW_MID = 0x36,
	FTILT_LOW = 0x37,
	UPTILT = 0x38,
	DOWNTILT = 0x39,
	FSMASH_MID = 0x3c,
	UPSMASH = 0x3f,
	DOWNSMASH = 0x40,
	NAIR = 0x41,
	FAIR = 0x42,
	BAIR = 0x43,
	UAIR = 0x44,
	DAIR = 0x45,
	SHIELD = 0xb3,
	SHIELD_STUN = 0xb5,
	SHIELD_REFLECT = 0xb6,
	GRAB = 0xd4,
	GRAB_RUNNING = 0xd6,
	AIRDODGE = 0xEC,
	EDGE_TEETERING_START = 0xF5, //Starting of edge teetering
	EDGE_TEETERING = 0xF6,
	SLIDING_OFF_EDGE = 0xfb, //When you get hit and slide off an edge
	EDGE_CATCHING = 0xFC, //Initial grabbing of edge, stuck in stun here
	EDGE_HANGING = 0xFD,
	EDGE_GETUP_QUICK = 0xFF, // < 100% damage
	EDGE_ATTACK_SLOW = 0x100, // < 100% damage
	EDGE_ATTACK_QUICK = 0x101, // >= 100% damage
	EGDE_ROLL_SLOW = 0x102, // >= 100% damage
	EDGE_ROLL_QUICK = 0x103, // < 100% damage
	EDGE_GETUP_SLOW = 0x104,  // >= 100% damage
	ENTRY = 0x142,	//Start of match. Can't move
	ENTRY_START = 0x143,	//Start of match. Can't move
	ENTRY_END = 0x144,	//Start of match. Can't move
	NEUTRAL_B_CHARGING = 0x156,
	NEUTRAL_B_ATTACKING = 0x157,
	SWORD_DANCE_1 = 0x15d,
	SWORD_DANCE_2_HIGH = 0x15e,
	SWORD_DANCE_2_MID = 0x15f,
	SWORD_DANCE_3_HIGH = 0x160,
	SWORD_DANCE_3_MID = 0x161,
	SWORD_DANCE_3_LOW = 0x162,
	SWORD_DANCE_4_HIGH = 0x163,
	SWORD_DANCE_4_MID = 0x164,
	SWORD_DANCE_4_LOW = 0x165,
	FIREFOX_WAIT_GROUND = 0x161, //Firefox wait on the ground
	FIREFOX_WAIT_AIR = 0x162, //Firefox wait in the air
	FIREFOX_GROUND = 0x163, //Firefox on the ground
	FIREFOX_AIR = 0x164, //Firefox in the air
	DOWN_B_GROUND = 0x169,
	DOWN_B_STUN = 0x16d, //Fox is stunned in these frames
	DOWN_B_AIR = 0x16e,
	UP_B_GROUND = 0x16f,
	UP_B = 0x170,	//The upswing of the UP-B. (At least for marth)
	MARTH_COUNTER = 0x171,
	MARTH_COUNTER_FALLING = 0x173,
};

enum MENU
{
	CHARACTER_SELECT = 33685760,
	STAGE_SELECT = 33685761,
	IN_GAME = 33685762,
	POSTGAME_SCORES = 33685764,
};

enum CHARACTER
{
	FOX = 0x0a,
	MEWTWO = 0x15,
	MARTH = 0x17,
};

#endif
