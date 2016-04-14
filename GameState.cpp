#include "GameState.h"

#include <iostream>
#include <string>
#include <iomanip>

using namespace std;

// TODO: this should be toString
void PrintMemory(GameMemory& memory)
{
    cout << "p1 percent: " << memory.player_one.percent << endl;
    cout << "p2 percent: " << memory.player_two.percent << endl;
    cout << "p1 stock: " << memory.player_one.stock << endl;
    cout << "p2 stock: " << memory.player_two.stock << endl;
    cout << "p1 character: " << memory.player_one.character << endl;
    cout << "p2 character: " << memory.player_two.character << endl;
    if(memory.player_one.facing)
    {
        cout << "p1 facing: right" << endl;
    }
    else
    {
        cout << "p1 facing: left" << endl;

    }
    if(memory.player_two.facing)
    {
        cout << "p2 facing: right" << endl;
    }
    else
    {
        cout << "p2 facing: left" << endl;
    }
    cout << "stage: " << hex << memory.stage << endl;
    cout << "frame: " << dec << memory.frame << endl;
    cout << "menu state: " << memory.menu_state << endl;
    cout << "p2 pointer x: " << memory.player_two_pointer_x << endl;
    cout << "p2 pointer y: " << memory.player_two_pointer_y << endl;

    cout << "p1 x: " << fixed << setprecision(10) << memory.player_one.x << endl;
    cout << "p1 y: " << fixed << setprecision(10) << memory.player_one.y << endl;

    cout << "p2 x: " << fixed << setprecision(10) << memory.player_two.x << endl;
    cout << "p2 y: " << fixed << setprecision(10) << memory.player_two.y << endl;

    cout << "p1 action: " << hex << memory.player_one.action << endl;
    cout << "p2 action: " << hex << memory.player_two.action << endl;

    cout << "p1 action count: " << dec << memory.player_one.action_counter << endl;
    cout << "p2 action count: " << dec << memory.player_two.action_counter << endl;

    cout << "p1 action frame: " << dec << memory.player_one.action_frame << endl;
    cout << "p2 action frame: " << dec << memory.player_two.action_frame << endl;

    if(memory.player_one.invulnerable)
    {
        cout << "p1 invulnerable" << endl;
    }
    else
    {
        cout << "p1 not invulnerable" << endl;
    }
    if(memory.player_two.invulnerable)
    {
        cout << "p2 invulnerable" << endl;
    }
    else
    {
        cout << "p2 not invulnerable" << endl;
    }

    if(memory.player_one.charging_smash)
    {
        cout << "p1 charging a smash" << endl;
    }
    else
    {
        cout << "p1 not charging a smash" << endl;
    }

    if(memory.player_two.charging_smash)
    {
        cout << "p2 charging a smash" << endl;
    }
    else
    {
        cout << "p2 not charging a smash" << endl;
    }

    cout << "p1 hitlag frames left: " << memory.player_one.hitlag_frames_left << endl;
    cout << "p2 hitlag frames left: " << memory.player_two.hitlag_frames_left << endl;

    cout << "p1 hitstun frames left: " << memory.player_one.hitstun_frames_left << endl;
    cout << "p2 hitstun frames left: " << memory.player_two.hitstun_frames_left << endl;

    cout << "p1 jumps left: " << memory.player_one.jumps_left << endl;
    cout << "p2 jumps left: " << memory.player_two.jumps_left << endl;

    if(memory.player_one.on_ground)
    {
        cout << "p1 on ground" << endl;
    }
    else
    {
        cout << "p1 in air" << endl;
    }
    if(memory.player_two.on_ground)
    {
        cout << "p2 on ground" << endl;
    }
    else
    {
        cout << "p2 in air" << endl;
    }

    cout << "p1 speed x air self: " << memory.player_one.speed_air_x_self << endl;
    cout << "p2 speed x air self: " << memory.player_two.speed_air_x_self << endl;

    cout << "p1 speed y self: " << memory.player_one.speed_y_self << endl;
    cout << "p2 speed y self: " << memory.player_two.speed_y_self << endl;

    cout << "p1 speed x attack: " << memory.player_one.speed_x_attack << endl;
    cout << "p2 speed x attack: " << memory.player_two.speed_x_attack << endl;

    cout << "p1 speed y attack: " << memory.player_one.speed_y_attack << endl;
    cout << "p2 speed y attack: " << memory.player_two.speed_y_attack << endl;

    cout << "p1 speed x ground self: " << memory.player_one.speed_ground_x_self << endl;
    cout << "p2 speed x ground self: " << memory.player_two.speed_ground_x_self << endl;
}

GameState* GameState::m_instance = NULL;

GameState *GameState::Instance()
{
    if (!m_instance)
    {
        m_instance = new GameState();
    }
    return m_instance;
}

GameState::GameState()
{
    m_memory = new GameMemory();
}

double GameState::getStageEdgePosition()
{
    double edge_position = 100;
    switch(m_memory->stage)
    {
        case BATTLEFIELD:
        {
            edge_position = 71.3078536987;
            break;
        }
        case FINAL_DESTINATION:
        {
            edge_position = 88.4735488892;
            break;
        }
        case DREAMLAND:
        {
            edge_position = 80.1791534424;
            break;
        }
        case FOUNTAIN_OF_DREAMS:
        {
            edge_position = 66.2554016113;
            break;
        }
    }
    return edge_position;
}

double GameState::getStageEdgeGroundPosition()
{
    double edge_position = 100;
    switch(m_memory->stage)
    {
        case BATTLEFIELD:
        {
            edge_position = 68.4000015259;
            break;
        }
        case FINAL_DESTINATION:
        {
            edge_position = 85.5656967163;
            break;
        }
        case DREAMLAND:
        {
            edge_position = 77.2713012695;
            break;
        }
        case FOUNTAIN_OF_DREAMS:
        {
            edge_position = 63.3475494385;
            break;
        }
    }
    return edge_position;
}

bool GameState::isDamageState(ACTION action)
{
    //Luckily, all the damage states are contiguous
    if(action >= DAMAGE_HIGH_1 && action <= DAMAGE_FLY_ROLL)
    {
        return true;
    }
    return false;
}

uint GameState::firstHitboxFrame(CHARACTER character, ACTION action)
{
    switch(character)
    {
        case MARTH:
        {
            switch(action)
            {
                case FSMASH_MID:
                {
                    return 10;
                }
                case DOWNSMASH:
                {
                    return 6;
                }
                case UPSMASH:
                {
                    return 13;
                }
                case DASH_ATTACK:
                {
                    return 12;
                }
                case GRAB:
                {
                    return 7;
                }
                case GRAB_RUNNING:
                {
                    return 10;
                }
                case FTILT_HIGH:
                case FTILT_HIGH_MID:
                case FTILT_MID:
                case FTILT_LOW_MID:
                case FTILT_LOW:
                {
                    return 7;
                }
                case UPTILT:
                {
                    return 7;
                }
                case DOWNTILT:
                {
                    return 7;
                }
                case SWORD_DANCE_1:
                case SWORD_DANCE_1_AIR:
                {
                    return 6;
                }
                case SWORD_DANCE_2_HIGH:
                case SWORD_DANCE_2_HIGH_AIR:
                {
                    return 12;
                }
                case SWORD_DANCE_2_MID:
                case SWORD_DANCE_2_MID_AIR:
                {
                    return 14;
                }
                case SWORD_DANCE_3_HIGH:
                case SWORD_DANCE_3_HIGH_AIR:
                {
                    return 13;
                }
                case SWORD_DANCE_3_MID:
                case SWORD_DANCE_3_MID_AIR:
                {
                    return 11;
                }
                case SWORD_DANCE_3_LOW:
                case SWORD_DANCE_3_LOW_AIR:
                {
                    return 15;
                }
                case SWORD_DANCE_4_HIGH:
                case SWORD_DANCE_4_HIGH_AIR:
                {
                    return 20;
                }
                case SWORD_DANCE_4_MID:
                case SWORD_DANCE_4_MID_AIR:
                {
                    return 23;
                }
                case SWORD_DANCE_4_LOW:
                case SWORD_DANCE_4_LOW_AIR:
                {
                    return 13;
                }
                case UP_B:
                case UP_B_GROUND:
                {
                    return 5;
                }
                case NAIR:
                {
                    return 6;
                }
                case UAIR:
                {
                    return 5;
                }
                case DAIR:
                {
                    return 6;
                }
                case BAIR:
                {
                    return 7;
                }
                case FAIR:
                {
                    return 4;
                }
                case NEUTRAL_ATTACK_1:
                {
                    return 4;
                }
                case NEUTRAL_ATTACK_2:
                {
                    return 6;
                }
                case NEUTRAL_B_ATTACKING:
                case NEUTRAL_B_ATTACKING_AIR:
                {
                    return 16;
                }
                case EDGE_ATTACK_SLOW:
                {
                    return 38;
                }
                case EDGE_ATTACK_QUICK:
                {
                    return 25;
                }
                default:
                {
                    return 0;
                    break;
                }
            }
            break;
        }
        default:
        {
            return 0;
            break;
        }
    }
}

uint GameState::lastHitboxFrame(CHARACTER character, ACTION action)
{
    switch(character)
    {
        case MARTH:
        {
            switch(action)
            {
                case FSMASH_MID:
                {
                    return 13;
                }
                case DOWNSMASH:
                {
                    return 23;
                }
                case UPSMASH:
                {
                    return 16;
                }
                case DASH_ATTACK:
                {
                    return 15;
                }
                case GRAB:
                {
                    return 8;
                }
                case GRAB_RUNNING:
                {
                    return 11;
                }
                case FTILT_HIGH:
                case FTILT_HIGH_MID:
                case FTILT_MID:
                case FTILT_LOW_MID:
                case FTILT_LOW:
                {
                    return 10;
                }
                case UPTILT:
                {
                    return 13;
                }
                case DOWNTILT:
                {
                    return 9;
                }
                case SWORD_DANCE_1:
                case SWORD_DANCE_1_AIR:
                {
                    return 8;
                }
                case SWORD_DANCE_2_HIGH:
                case SWORD_DANCE_2_HIGH_AIR:
                {
                    return 15;
                }
                case SWORD_DANCE_2_MID:
                case SWORD_DANCE_2_MID_AIR:
                {
                    return 16;
                }
                case SWORD_DANCE_3_HIGH:
                case SWORD_DANCE_3_HIGH_AIR:
                {
                    return 17;
                }
                case SWORD_DANCE_3_MID:
                case SWORD_DANCE_3_MID_AIR:
                {
                    return 14;
                }
                case SWORD_DANCE_3_LOW:
                case SWORD_DANCE_3_LOW_AIR:
                {
                    return 18;
                }
                case SWORD_DANCE_4_HIGH:
                case SWORD_DANCE_4_HIGH_AIR:
                {
                    return 25;
                }
                case SWORD_DANCE_4_MID:
                case SWORD_DANCE_4_MID_AIR:
                {
                    return 26;
                }
                case SWORD_DANCE_4_LOW:
                case SWORD_DANCE_4_LOW_AIR:
                {
                    return 38;
                }
                case UP_B:
                case UP_B_GROUND:
                {
                    return 10;
                }
                case NAIR:
                {
                    return 21;
                }
                case UAIR:
                {
                    return 8;
                }
                case DAIR:
                {
                    return 9;
                }
                case BAIR:
                {
                    return 11;
                }
                case FAIR:
                {
                    return 7;
                }
                case NEUTRAL_ATTACK_1:
                {
                    return 7;
                }
                case NEUTRAL_ATTACK_2:
                {
                    return 10;
                }
                case NEUTRAL_B_ATTACKING:
                case NEUTRAL_B_ATTACKING_AIR:
                {
                    return 21;
                }
                case EDGE_ATTACK_SLOW:
                {
                    return 41;
                }
                case EDGE_ATTACK_QUICK:
                {
                    return 28;
                }
                default:
                {
                    return 0;
                    break;
                }
            }
            break;
        }
        default:
        {
            return 0;
            break;
        }
    }
}


uint GameState::landingLag(CHARACTER character, ACTION action)
{
    switch(character)
    {
        case MARTH:
        {
            switch(action)
            {
                case NAIR:
                {
                    return 7;
                }
                case FAIR:
                {
                    return 7;
                }
                case BAIR:
                {
                    return 12;
                }
                case UAIR:
                {
                    return 7;
                }
                case DAIR:
                {
                    return 16;
                }
                default:
                {
                    return 0;
                }
            }
        }
        default:
        {
            return 0;
        }
    }
}

uint GameState::totalActionFrames(CHARACTER character, ACTION action)
{
    switch(character)
    {
        case MARTH:
        {
            switch(action)
            {
                case FSMASH_MID:
                {
                    return 47;
                }
                case DOWNSMASH:
                {
                    return 61;
                }
                case UPSMASH:
                {
                    return 45;
                }
                case DASH_ATTACK:
                {
                    return 40;
                }
                case GRAB:
                {
                    return 30;
                }
                case GRAB_RUNNING:
                {
                    return 40;
                }
                case FTILT_HIGH:
                case FTILT_HIGH_MID:
                case FTILT_MID:
                case FTILT_LOW_MID:
                case FTILT_LOW:
                {
                    return 35;
                }
                case UPTILT:
                {
                    return 31;
                }
                case DOWNTILT:
                {
                    return 19;
                }
                case SWORD_DANCE_1_AIR:
                case SWORD_DANCE_1:
                {
                    return 29;
                }
                case SWORD_DANCE_2_HIGH_AIR:
                case SWORD_DANCE_2_MID_AIR:
                case SWORD_DANCE_2_HIGH:
                case SWORD_DANCE_2_MID:
                {
                    return 40;
                }
                case SWORD_DANCE_3_HIGH_AIR:
                case SWORD_DANCE_3_MID_AIR:
                case SWORD_DANCE_3_LOW_AIR:
                case SWORD_DANCE_3_HIGH:
                case SWORD_DANCE_3_MID:
                case SWORD_DANCE_3_LOW:
                {
                    return 46;
                }
                case SWORD_DANCE_4_HIGH:
                case SWORD_DANCE_4_MID:
                case SWORD_DANCE_4_HIGH_AIR:
                case SWORD_DANCE_4_MID_AIR:
                {
                    return 50;
                }
                case SWORD_DANCE_4_LOW:
                case SWORD_DANCE_4_LOW_AIR:
                {
                    return 60;
                }
                case UP_B:
                case UP_B_GROUND:
                {
                    return 10;
                }
                case NAIR:
                {
                    return 21;
                }
                case UAIR:
                {
                    return 25;
                }
                case DAIR:
                {
                    return 48;
                }
                case BAIR:
                {
                    return 32;
                }
                case FAIR:
                {
                    return 27;
                }
                case NEUTRAL_ATTACK_1:
                {
                    return 19;
                }
                case NEUTRAL_ATTACK_2:
                {
                    return 19;
                }
                case NEUTRAL_B_ATTACKING:
                case NEUTRAL_B_ATTACKING_AIR:
                {
                    return 44;
                }
                case EDGE_ATTACK_SLOW:
                {
                    return 68;
                }
                case EDGE_ATTACK_QUICK:
                {
                    return 54;
                }
                case LANDING_SPECIAL:
                {
                    if(m_landingFromUpB)
                    {
                        return 30;
                    }
                    else
                    {
                        return 10;
                    }
                }
                case MARTH_COUNTER:
                {
                    return 59;
                }
                case SPOTDODGE:
                {
                    return 27;
                }
                default:
                {
                    return 0;
                    break;
                }
            }
            break;
        }
        default:
        {
            return 0;
            break;
        }
    }
}

void GameState::setLandingState(bool state)
{
    m_landingFromUpB = state;
}

bool GameState::isAttacking(ACTION action)
{
    switch(action)
    {
        case FSMASH_MID:
        case DOWNSMASH:
        case UPSMASH:
        case DASH_ATTACK:
        case GRAB:
        case GRAB_RUNNING:
        case FTILT_HIGH:
        case FTILT_HIGH_MID:
        case FTILT_MID:
        case FTILT_LOW_MID:
        case FTILT_LOW:
        case UPTILT:
        case DOWNTILT:
        case SWORD_DANCE_1:
        case SWORD_DANCE_2_HIGH:
        case SWORD_DANCE_2_MID:
        case SWORD_DANCE_3_HIGH:
        case SWORD_DANCE_3_MID:
        case SWORD_DANCE_3_LOW:
        case SWORD_DANCE_4_HIGH:
        case SWORD_DANCE_4_MID:
        case SWORD_DANCE_4_LOW:
        case SWORD_DANCE_1_AIR:
        case SWORD_DANCE_2_HIGH_AIR:
        case SWORD_DANCE_2_MID_AIR:
        case SWORD_DANCE_3_HIGH_AIR:
        case SWORD_DANCE_3_MID_AIR:
        case SWORD_DANCE_3_LOW_AIR:
        case SWORD_DANCE_4_HIGH_AIR:
        case SWORD_DANCE_4_MID_AIR:
        case SWORD_DANCE_4_LOW_AIR:
        case UP_B:
        case UP_B_GROUND:
        case NAIR:
        case UAIR:
        case DAIR:
        case BAIR:
        case FAIR:
        case NEUTRAL_ATTACK_1:
        case NEUTRAL_ATTACK_2:
        case NEUTRAL_ATTACK_3:
        case NEUTRAL_B_ATTACKING:
        case NEUTRAL_B_ATTACKING_AIR:
        case EDGE_ATTACK_QUICK:
        case EDGE_ATTACK_SLOW:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}

bool GameState::isReverseHit(ACTION action)
{
    switch(action)
    {
        case DOWNSMASH:
        case UPSMASH:
        case GRAB_RUNNING:
        case UPTILT:
        case NAIR:
        case UAIR:
        case DAIR:
        case BAIR:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}
