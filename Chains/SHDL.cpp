#include "SHDL.h"

void SHDL::PressButtons()
{
    m_startingFrame = 0;

    switch(m_state->frame % 27)
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

SHDL::SHDL(GameState *state) : Chain(state)
{
    m_controller = Controller::Instance();
}

SHDL::~SHDL()
{
}
