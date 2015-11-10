#include "SHDL.h"

void SHDL::PressButtons()
{
    uint frame = m_state->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Jump
            m_controller->pressButton(Controller::BUTTON_Y);
            break;
        }
        case 1:
        {
            //let go of jump
            m_controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
        case 3:
        {
            //Laser
            m_controller->pressButton(Controller::BUTTON_B);
            break;
        }
        case 4:
        {
            //let go of Laser
            m_controller->releaseButton(Controller::BUTTON_B);
            break;
        }
        case 6:
        {
            //Laser
            m_controller->pressButton(Controller::BUTTON_B);
            break;
        }
        case 17:
        {
            //let go of Laser
            m_controller->releaseButton(Controller::BUTTON_B);
            break;
        }
    }
}

bool SHDL::IsInterruptible()
{
    uint frame = m_state->frame - m_startingFrame;
    if(frame >= 27)
    {
        return true;
    }
    return false;
}

SHDL::SHDL(GameState *state) : Chain(state)
{
    m_startingFrame = m_state->frame;
    m_controller = Controller::Instance();
}

SHDL::~SHDL()
{
}
