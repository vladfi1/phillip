#include "JumpCanceledShine.h"

JumpCanceledShine::JumpCanceledShine()
{
    m_startingFrame = m_state->m_memory->frame;
}

JumpCanceledShine::~JumpCanceledShine()
{
}

bool JumpCanceledShine::IsInterruptible()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 8)
    {
        return true;
    }
    return false;
}

void JumpCanceledShine::PressButtons()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Down-B
            m_controller->pressButton(Controller::BUTTON_B);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            break;
        }
        case 6:
        {
            //Let go of Down-B
            m_controller->releaseButton(Controller::BUTTON_B);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);

            //Jump
            m_controller->pressButton(Controller::BUTTON_Y);

            break;
        }
        case 7:
        {
            //Let go of Jump
            m_controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
    }
}
