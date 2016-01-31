#include <cmath>

#include "SpotDodge.h"

void SpotDodge::PressButtons()
{
    //If we're medium range or more, and reverse-facing, don't bother doing anything.
    float distance = std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x);
    if(m_isReverseFacing && (distance > 18))
    {
        m_controller->emptyInput();
        return;
    }

    switch(m_state->m_memory->player_one_action_frame)
    {
        case 1:
        {
            //Spot dodge
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            m_controller->pressButton(Controller::BUTTON_L);
            break;
        }
        case 2:
        {
            //down
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            break;
        }
        case 3:
        {
            //let go
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            m_controller->releaseButton(Controller::BUTTON_L);
            break;
        }
    }
}

//We're always interruptible during a Walk
bool SpotDodge::IsInterruptible()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 23)
    {
        return true;
    }
    return false;
}

SpotDodge::SpotDodge()
{
    bool player_one_is_to_the_left = (m_state->m_memory->player_one_x - m_state->m_memory->player_two_x > 0);
    if(m_state->m_memory->player_one_facing != player_one_is_to_the_left)
    {
        m_isReverseFacing = false;
    }
    else
    {
        m_isReverseFacing = true;
    }
}

SpotDodge::~SpotDodge()
{
}
