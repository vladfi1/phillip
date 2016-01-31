#include <cmath>

#include "Powershield.h"
void Powershield::PressButtons()
{
    //What frame (relative to the start of the attack) we should be shielding on?
    uint shield_on_frame = 0;
    double distance = pow(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x), 2);
    distance += pow(std::abs(m_state->m_memory->player_one_y - m_state->m_memory->player_two_y), 2);
    distance = sqrt(distance);

    //Determine when to shield depending on distance and what attack it is
    switch(m_state->m_memory->player_one_action)
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
                    shield_on_frame = 4;
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
                    shield_on_frame = 3;
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
        case SWORD_DANCE_1_AIR:
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
        case SWORD_DANCE_2_MID_AIR:
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
        case SWORD_DANCE_3_MID_AIR:
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
        case SWORD_DANCE_3_LOW_AIR:
        {
            shield_on_frame = 12;
            break;
        }
        case SWORD_DANCE_3_HIGH:
        case SWORD_DANCE_3_HIGH_AIR:
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
        case SWORD_DANCE_4_MID_AIR:
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
        case SWORD_DANCE_4_HIGH_AIR:
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
            shield_on_frame = 3;
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
        //TODO maybe consider NAIR reverse hit
        case NAIR:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 3;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 3;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 60;
            }
            break;
        }
        case NEUTRAL_ATTACK_1:
        {
            shield_on_frame = 3;
            break;
        }
        case NEUTRAL_ATTACK_2:
        {
            shield_on_frame = 3;
            break;
        }
        case NEUTRAL_B_ATTACKING_AIR:
        case NEUTRAL_B_ATTACKING:
        {
            //If we're right in close
            if(distance < 18)
            {
                shield_on_frame = 2;
            }
            //Mid distance
            else if(distance >= 18 && distance < 27)
            {
                shield_on_frame = 2;
            }
            //Long distance
            else if(distance >= 27)
            {
                shield_on_frame = 3;
            }
            break;
        }
        default:
        {
            //If we get an unknown input, then let go of shield (in case we were holding) and become interruptible
            m_controller->emptyInput();
            m_endEarly = true;
            return;
        }
    }

    //If we're the right number of frames past the start of the attack, let's shield
    if(!m_hasShielded && (m_state->m_memory->player_one_action_frame >= shield_on_frame))
    {
        m_hasShielded = true;
        m_frameShielded = m_state->m_memory->frame;
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->pressButton(Controller::BUTTON_L);
    }
    //4 frames later, let go of shield
    else if(m_state->m_memory->frame >= (m_frameShielded + 4))
    {
        //If it's a neutral-air, just hold onto shield until the attack is over
        if(m_state->m_memory->player_one_action == NAIR &&
            m_state->m_memory->frame < m_frameShielded + 19)
        {
            return;
        }
        m_letGo = true;
        m_controller->releaseButton(Controller::BUTTON_L);
    }
}

bool Powershield::IsInterruptible()
{
    if(m_endEarly)
    {
        return true;
    }

    if(m_state->m_memory->player_two_action == SHIELD ||
        m_state->m_memory->player_two_action == SHIELD_REFLECT)
    {
        return false;
    }

    //Don't interrupt if we are waiting to let go of shield
    if(m_hasShielded && !m_letGo)
    {
        return false;
    }
    return true;
}

Powershield::Powershield()
{
    m_hasShielded = false;
    m_letGo = false;
    m_frameShielded = -100;
    bool player_one_is_to_the_left = (m_state->m_memory->player_one_x - m_state->m_memory->player_two_x > 0);
    m_endEarly = false;
    if(m_state->m_memory->player_one_facing != player_one_is_to_the_left)
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
