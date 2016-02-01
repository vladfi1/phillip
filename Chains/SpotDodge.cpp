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

    if(m_state->m_memory->player_two_action == SHIELD ||
        m_state->m_memory->player_two_action == SHIELD_START ||
        m_state->m_memory->player_two_action == SHIELD_REFLECT)
    {
        m_hasShielded = true;
    }

    if(!m_hasShielded)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->pressButton(Controller::BUTTON_L);
        return;
    }

    if(!m_hasSpotDodged && m_state->m_memory->player_two_action == SHIELD_REFLECT)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
        m_hasSpotDodged = true;
        return;
    }

    m_controller->emptyInput();
}

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
    m_startingFrame = m_state->m_memory->frame;
    m_hasShielded = false;
    m_hasSpotDodged = false;
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
