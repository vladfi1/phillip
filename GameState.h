#ifndef GAMESTATE_H
#define GAMESTATE_H

#include <sys/types.h>

struct GameMemory
{
    uint player_one_percent;
    uint player_one_stock;
    //True is right, false is left
    bool player_one_facing;
    float player_one_x;
    float player_one_y;
    uint player_one_action;
    uint player_one_action_counter;
    uint player_one_action_frame;
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
    uint player_two_action_frame;
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
    uint stage;
};

enum ACTION
{
    DEAD_DOWN = 0x0,
    DEAD_LEFT = 0x1,
    DEAD_RIGHT = 0x2,
    DEAD_FLY_STAR = 0x4,
    DEAD_FLY = 0x6, //When you have been hit upwards and are dead
    DEAD_FLY_SPLATTER = 0x7, //Hit upwards and have splattered on the camera
    DEAD_FLY_SPLATTER_FLAT = 0x8, //Hit upwards and have splattered on the camera
    ON_HALO_DESCENT = 0xc,
    ON_HALO_WAIT = 0x0d,
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
    FALLING = 0x1D,    //The "wait" state of the air.
    DEAD_FALL = 0x23, //Falling after up-b
    CROUCH_START = 0x27, //Going from stand to crouch
    CROUCHING = 0x28,
    CROUCH_END = 0x29, //Standing up from crouch
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
    NAIR_LANDING  = 0x46,
    FAIR_LANDING  = 0x47,
    BAIR_LANDING  = 0x48,
    UAIR_LANDING  = 0x49,
    DAIR_LANDING  = 0x4a,
    DAMAGE_HIGH_1 = 0x4b,
    DAMAGE_HIGH_2 = 0x4c,
    DAMAGE_HIGH_3 = 0x4d,
    DAMAGE_NEUTRAL_1 = 0x4e,
    DAMAGE_NEUTRAL_2 = 0x4f,
    DAMAGE_NEUTRAL_3 = 0x50,
    DAMAGE_LOW_1 = 0x51,
    DAMAGE_LOW_2 = 0x52,
    DAMAGE_LOW_3 = 0x53,
    DAMAGE_AIR_1 = 0x54,
    DAMAGE_AIR_2 = 0x55,
    DAMAGE_AIR_3 = 0x56,
    DAMAGE_FLY_HIGH = 0x57,
    DAMAGE_FLY_NEUTRAL = 0x58,
    DAMAGE_FLY_LOW = 0x59,
    DAMAGE_FLY_TOP = 0x5a,
    DAMAGE_FLY_ROLL = 0x5b,
    SHIELD_START = 0xb2,
    SHIELD = 0xb3,
    SHIELD_RELEASE = 0xb4,
    SHIELD_STUN = 0xb5,
    SHIELD_REFLECT = 0xb6,
    GRAB = 0xd4,
    GRAB_RUNNING = 0xd6,
    ROLL_FORWARD = 0xe9,
    ROLL_BACKWARD = 0xea,
    SPOTDODGE = 0xEB,
    AIRDODGE = 0xEC,
    EDGE_TEETERING_START = 0xF5, //Starting of edge teetering
    EDGE_TEETERING = 0xF6,
    SLIDING_OFF_EDGE = 0xfb, //When you get hit and slide off an edge
    EDGE_CATCHING = 0xFC, //Initial grabbing of edge, stuck in stun here
    EDGE_HANGING = 0xFD,
    EDGE_GETUP_SLOW = 0xFE,  // >= 100% damage
    EDGE_GETUP_QUICK = 0xFF, // < 100% damage
    EDGE_ATTACK_SLOW = 0x100, // < 100% damage
    EDGE_ATTACK_QUICK = 0x101, // >= 100% damage
    EDGE_ROLL_SLOW = 0x102, // >= 100% damage
    EDGE_ROLL_QUICK = 0x103, // < 100% damage
    ENTRY = 0x142,    //Start of match. Can't move
    ENTRY_START = 0x143,    //Start of match. Can't move
    ENTRY_END = 0x144,    //Start of match. Can't move
    NEUTRAL_B_CHARGING = 0x156,
    NEUTRAL_B_ATTACKING = 0x157,
    NEUTRAL_B_CHARGING_AIR = 0x15A,
    NEUTRAL_B_ATTACKING_AIR = 0x15B,
    SWORD_DANCE_1 = 0x15d,
    SWORD_DANCE_2_HIGH = 0x15e,
    SWORD_DANCE_2_MID = 0x15f,
    SWORD_DANCE_3_HIGH = 0x160,
    SWORD_DANCE_3_MID = 0x161,
    SWORD_DANCE_3_LOW = 0x162,
    SWORD_DANCE_4_HIGH = 0x163,
    SWORD_DANCE_4_MID = 0x164,
    SWORD_DANCE_4_LOW = 0x165,
    SWORD_DANCE_1_AIR = 0x166,
    SWORD_DANCE_2_HIGH_AIR = 0x167,
    SWORD_DANCE_2_MID_AIR = 0x168,
    SWORD_DANCE_3_HIGH_AIR = 0x169,
    SWORD_DANCE_3_MID_AIR = 0x16a,
    SWORD_DANCE_3_LOW_AIR = 0x16b,
    SWORD_DANCE_4_HIGH_AIR = 0x16c,
    SWORD_DANCE_4_MID_AIR = 0x16d,
    SWORD_DANCE_4_LOW_AIR = 0x16e,
    FIREFOX_WAIT_GROUND = 0x161, //Firefox wait on the ground
    FIREFOX_WAIT_AIR = 0x162, //Firefox wait in the air
    FIREFOX_GROUND = 0x163, //Firefox on the ground
    FIREFOX_AIR = 0x164, //Firefox in the air
    DOWN_B_GROUND_START = 0x168,
    DOWN_B_GROUND = 0x169,
    DOWN_B_STUN = 0x16d, //Fox is stunned in these frames
    DOWN_B_AIR = 0x16e,
    UP_B_GROUND = 0x16f,
    UP_B = 0x170,    //The upswing of the UP-B. (At least for marth)
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

enum STAGE
{
    BATTLEFIELD = 0x18,
    FINAL_DESTINATION = 0x19,
    DREAMLAND = 0x1a,
    FOUNTAIN_OF_DREAMS = 0x8,
};

class GameState {
public:
    static GameState *Instance();

    //This is the x coordinate of the edge, as you would be hanging from the edge, off the stage
    double getStageEdgePosition();
    //This is the x coordinate of the edge, as you would be teetering while standing on the stage
    double getStageEdgeGroundPosition();

    bool isDamageState(ACTION);

    //Returns the frame of the first hitbox
    //    return value of 0 means not an attack, or not supported yet
    uint firstHitboxFrame(CHARACTER, ACTION);

    //Returns the frame of the last hitbox
    //    return value of 0 means not an attack, or not supported yet
    uint lastHitboxFrame(CHARACTER, ACTION);

    //Returns the number of frames in the animation total
    //    Note that this returns the number of frames they are guaranteed to be in, so IASA frames are cut off
    //    return value of 0 means not an attack, or not supported yet
    uint totalActionFrames(CHARACTER, ACTION);

    //Returns the amount of landing lag from the given airial attack
    //    return value of 0 means not an airial attack, or not supported yet
    uint landingLag(CHARACTER, ACTION);

    //Is the current landing special state from UP-B (true) or wavedash (false)
    void setLandingState(bool);

    //Is the given action an attack?
    bool isAttacking(ACTION a);
    //Does the given attack have reverse hit frames? (Do we need to worry about parrying from attacks if the
    //  enemy is facing the other way?)
    bool isReverseHit(ACTION a);

    GameMemory *m_memory;

private:
    GameState();
    static GameState *m_instance;
    bool m_landingFromUpB;
};

#endif
