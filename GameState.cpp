#include "GameState.h"

#include <string>

GameState* GameState::m_instance = NULL;

GameState *GameState::Instance()
{
    if (!m_instance)
    {
        m_instance = new GameState();
    }
    return m_instance;
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

bool GameState::isDamageState(ACTION action)
{
    //Luckily, all the damage states are contiguous
    if(action >= DAMAGE_HIGH_1 && action <= DAMAGE_FLY_ROLL)
    {
        return true;
    }
    return false;
}


GameState::GameState()
{

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
                {
                    return 6;
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
                //TODO: I don't have an animation for this...
                case NEUTRAL_ATTACK_3:
                {
                    return 6;
                }
                case NEUTRAL_B_ATTACKING:
                case NEUTRAL_B_ATTACKING_AIR:
                {
                    return 16;
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
