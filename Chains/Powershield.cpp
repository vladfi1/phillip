#include <cmath>

#include "Powershield.h"

void Powershield::PressButtons()
{
    int shield_on_frame = 0;
    uint distance = std::abs(m_state->player_one_x - m_state->player_two_x);
    //If we're right in close
    if(distance < 18)
    {
        shield_on_frame = 7;
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

    //If we're 7 frames past the start of the fsmash, let's shield
    if(m_state->frame == m_startingFrame + shield_on_frame)
    {
        m_frame_shielded = m_state->frame;
        m_controller->pressButton(Controller::BUTTON_L);
    }
    if(m_state->frame == m_startingFrame + shield_on_frame + 4)
    {
        m_frame_shielded = m_state->frame;
        m_controller->releaseButton(Controller::BUTTON_L);
    }
}

bool Powershield::IsInterruptible()
{
    if(m_frame_shielded > 0 && m_state->frame > m_frame_shielded)
    {
        return true;
    }
    return false;
}

Powershield::Powershield(GameState *state) : Chain(state)
{
    m_startingFrame = m_state->frame;
    m_frame_shielded = 0;
    m_controller = Controller::Instance();
}

Powershield::~Powershield()
{
}
