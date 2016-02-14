#include "ShortHopLaser.h"
#include "TransitionHelper.h"

void ShortHopLaser::PressButtons()
{
    bool isOnRight = m_state->m_memory->player_one_x < m_state->m_memory->player_two_x;

    switch(m_direction)
    {
        case RETREATING:
        {
            //Dash away from the opponent
            if(m_state->m_memory->player_two_action == STANDING)
            {
                m_controller->releaseButton(Controller::BUTTON_Y);
                m_controller->releaseButton(Controller::BUTTON_B);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 1 : 0, .5);
                return;
            }
            //If we're moving, then jump
            if(m_state->m_memory->player_two_action == DASHING ||
                m_state->m_memory->player_two_action == WALK_SLOW ||
                m_state->m_memory->player_two_action == WALK_MIDDLE ||
                m_state->m_memory->player_two_action == WALK_FAST ||
                m_state->m_memory->player_two_action == RUNNING ||
                m_state->m_memory->player_two_action == TURNING)
            {
                //If we're dashing inwards, then just turn around, don't jump
                //  (The jump doesn't count if we press it here.)
                if(m_state->m_memory->player_two_action == DASHING &&
                    m_state->m_memory->player_two_facing != isOnRight)
                {
                    m_controller->releaseButton(Controller::BUTTON_Y);
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 1 : 0, .5);
                    return;
                }

                m_controller->pressButton(Controller::BUTTON_Y);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 1 : 0, .5);
                return;
            }
            break;
        }
        case APPROACHING:
        {
            //Dash away from the opponent
            if(m_state->m_memory->player_two_action == STANDING)
            {
                m_controller->releaseButton(Controller::BUTTON_Y);
                m_controller->releaseButton(Controller::BUTTON_B);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 0 : 1, .5);
                return;
            }

            //If we're already approaching, then jump
            if(m_state->m_memory->player_two_action == DASHING ||
                m_state->m_memory->player_two_action == WALK_SLOW ||
                m_state->m_memory->player_two_action == WALK_MIDDLE ||
                m_state->m_memory->player_two_action == WALK_FAST)
            {

                if(m_state->m_memory->player_two_facing != isOnRight)
                {
                    m_controller->pressButton(Controller::BUTTON_Y);
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 0 : 1, .5);
                    return;
                }
                else
                {
                    //If we're moving the wrong way, turn around
                    m_controller->releaseButton(Controller::BUTTON_Y);
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 0 : 1, .5);
                }
            }
            break;
        }
        case UNMOVING:
        {
            //Dash away from the opponent
            if(m_state->m_memory->player_two_action == DASHING||
                m_state->m_memory->player_two_action == WALK_SLOW ||
                m_state->m_memory->player_two_action == WALK_MIDDLE ||
                m_state->m_memory->player_two_action == WALK_FAST)
            {
                m_controller->emptyInput();
                return;
            }
            //If we're standing, then jump
            if(m_state->m_memory->player_two_action == STANDING)
            {
                m_controller->pressButton(Controller::BUTTON_Y);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
                return;
            }
            break;
        }
    }
    //Let go of jump once we're in knee bend
    if(m_state->m_memory->player_two_action == KNEE_BEND)
    {
        m_controller->releaseButton(Controller::BUTTON_Y);
        m_controller->releaseButton(Controller::BUTTON_B);
        return;
    }
    //Once we're jumping, turn around
    if(!m_state->m_memory->player_two_on_ground &&
        m_pressedBack == false)
    {
        m_pressedBack = true;
        if(m_direction == RETREATING)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, isOnRight ? 0 : 1, .5);
            return;
        }
    }
    //Once we're done turning around in the air, start to laser
    if(!m_state->m_memory->player_two_on_ground &&
        m_pressedBack == true &&
        m_state->m_memory->player_two_speed_y_self < 0)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->pressButton(Controller::BUTTON_B);
        return;
    }
    //Once we're falling, fast fall it
    if(m_state->m_memory->player_two_speed_y_self < 0)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
        return;
    }
    //If we're landing from laser, let go of the controller
    if(m_state->m_memory->player_two_action == LANDING_SPECIAL)
    {
        m_controller->emptyInput();
        return;
    }
}

bool ShortHopLaser::IsInterruptible()
{
    if(m_state->m_memory->player_two_action == LANDING ||
        m_state->m_memory->player_two_action == CROUCHING)
    {
        return true;
    }

    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 60)
    {
        //Emergency backup kill for the chain in case we get stuck here somehow
        return true;
    }
    return false;
}

ShortHopLaser::ShortHopLaser(DIRECTION direction)
{
    m_direction = direction;
    m_pressedBack = false;
}

ShortHopLaser::~ShortHopLaser()
{
}
