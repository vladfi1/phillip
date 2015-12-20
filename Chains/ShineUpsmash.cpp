#include "ShineUpsmash.h"

void ShineUpsmash::PressButtons()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Shine
            m_controller->pressButton(Controller::BUTTON_B);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            break;
        }
        case 5:
        {
            //Let go of down b
            m_controller->releaseButton(Controller::BUTTON_B);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            //Jump out of our shine
            m_controller->pressButton(Controller::BUTTON_Y);
            break;
        }
        case 6:
        {
            m_controller->releaseButton(Controller::BUTTON_Y);

            //Upsmash
            m_controller->tiltAnalog(Controller::BUTTON_C, .5, 1);
            break;
        }
        case 7:
        {
            //Let go of upsmash
            m_controller->tiltAnalog(Controller::BUTTON_C, .5, .5);
            break;
        }
    }
}

bool ShineUpsmash::IsInterruptible()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    //TODO upsmash is 39 frames, plus the 6 (5?) of the shine and jump
    if(frame >= 45)
    {
        return true;
    }
    return false;
}

ShineUpsmash::ShineUpsmash()
{
    m_startingFrame = m_state->m_memory->frame;
}

ShineUpsmash::~ShineUpsmash()
{
}
