#include "Jab.h"

void Jab::PressButtons()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Jab
            m_controller->pressButton(Controller::BUTTON_A);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            break;
        }
        case 1:
        {
            //Let go of jab
            m_controller->releaseButton(Controller::BUTTON_A);
            break;
        }
    }
}

bool Jab::IsInterruptible()
{
    if(m_state->m_memory->player_two_action == STANDING)
    {
        return true;
    }

    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 18)
    {
        return true;
    }
    return false;
}

Jab::Jab()
{
    m_startingFrame = m_state->m_memory->frame;
}

Jab::~Jab()
{
}
