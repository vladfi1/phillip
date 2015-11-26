#include <cmath>

#include "Powershield.h"

void Powershield::PressButtons()
{
    //What frame (relative to the start of the attack) we should be shielding on
    int shield_on_frame = 0;
    float distance = std::abs(m_state->player_one_x - m_state->player_two_x);
    //Determine when to shield depending on distance and what attack it is
    switch(m_state->player_one_action)
    {
        case FSMASH_MID:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 6;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 7;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 8;
            }
            break;
        }
        case UPSMASH:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 10;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 10;
            }
            //There is no long distance upsmash hit, so just set this high
            else if(distance >= 27)
            {
                shield_on_frame = 100;
            }
            break;
        }
        case DOWNSMASH:
        {
            if(m_isReverseFacing)
            {
                shield_on_frame = 18;
            }
            else
            {
                //If we're right in close
                if(distance < 18)
                {
                    shield_on_frame = 3;
                }
                //Mid distance
                else if(distance >= 18 && distance < 27)
                {
                    shield_on_frame = 4;
                }
                //There is no long distance upsmash hit, so just set this high
                else if(distance >= 27)
                {
                    shield_on_frame = 4;
                }
            }
            break;
        }
        case FTILT_MID:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 4;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 5;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 6;
            }
            break;
        }
        case DOWNTILT:
        {
            shield_on_frame = 4;
            break;
        }
        case UPTILT:
        {
            if(m_isReverseFacing)
            {
                shield_on_frame = 8;
            }
            else
            {
                //If we're right in close
                if(distance < 18)
                {
                    shield_on_frame = 3;
                }
                //Mid distance
                else if(distance >= 18 && distance < 27)
                {
                    shield_on_frame = 4;
                }
                //Long distance
                else if(distance >= 27)
                {
                    shield_on_frame = 60;
                }
            }
            break;
        }
        case DASH_ATTACK:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 9;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 10;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 10;
            }
            break;
        }
        case SWORD_DANCE_1:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 3;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 4;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 4;
            }
            break;
        }
        case SWORD_DANCE_2_MID:
        {
            shield_on_frame = 11;
            break;
        }
        case SWORD_DANCE_2_HIGH:
        {
            shield_on_frame = 9;
            break;
        }
        case SWORD_DANCE_3_MID:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 8;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 8;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 9;
            }
            break;
        }
        case SWORD_DANCE_3_LOW:
        {
            shield_on_frame = 12;
            break;
        }
        case SWORD_DANCE_3_HIGH:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 10;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 11;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 11;
            }
            break;
        }
        case SWORD_DANCE_4_MID:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 20;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 21;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 21;
            }
            break;
        }
        case SWORD_DANCE_4_HIGH:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 20;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 21;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 21;
            }
            break;
        }
        case UP_B:
        case UP_B_GROUND:
        {
            if(distance >= 27)
            {
                shield_on_frame = 60;
            }
            shield_on_frame = 2;
            break;
        }
        case FAIR:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 1;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 2;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 2;
            }
            break;
        }
        case BAIR:
        {
            shield_on_frame = 4;
            break;
        }
        case DAIR:
        {
            if(m_isReverseFacing)
            {
                shield_on_frame = 5;
            }
            else
            {
                shield_on_frame = 3;
            }
            break;
        }
        case UAIR:
        {
            if(distance > 27)
            {
                shield_on_frame = 60;
                break;
            }
            if(m_isReverseFacing)
            {
                shield_on_frame = 5;
            }
            else
            {
                shield_on_frame = 2;
            }
            break;
        }
        case NEUTRAL_ATTACK_1:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 1;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 2;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 60;
            }
            break;
        }
        case NEUTRAL_ATTACK_2:
        {
            if(distance >= 27)
            {
                shield_on_frame = 60;
            }
            shield_on_frame = 3;
            break;
        }
        default:
        {
            m_controller->emptyInput();
            return;
        }
    }

    //If we're the right number of frames past the start of the attack, let's shield
    if(m_state->frame == (m_startFrame + shield_on_frame))
    {
        m_controller->pressButton(Controller::BUTTON_L);
    }
    //4 frames later, let go of shield
    else if(m_state->frame == (m_startFrame + shield_on_frame + 4))
    {
        m_frame_shielded = m_state->frame;
        m_controller->releaseButton(Controller::BUTTON_L);
    }
}

bool Powershield::IsInterruptible()
{
    if((m_state->player_two_action != SHIELD_STUN) && (m_state->player_two_action != SHIELD))
    {
        return true;
    }
    return false;
}

Powershield::Powershield(GameState *state, uint startFrame) : Chain(state)
{
    m_frame_shielded = 0;
    m_startFrame = startFrame;
    m_controller = Controller::Instance();
    bool player_one_is_to_the_left = (m_state->player_one_x - m_state->player_two_x > 0);
    if(m_state->player_one_facing != player_one_is_to_the_left)
    {
        m_isReverseFacing = false;
    }
    else
    {
        m_isReverseFacing = true;
    }
}

Powershield::~Powershield()
{
}
