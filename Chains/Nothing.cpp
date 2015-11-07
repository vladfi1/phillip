#include "Nothing.h"

void Nothing::PressButtons()
{
    //Just send this once. Not every frame
    //Reset the controller blamk
    if(!m_reset)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->tiltAnalog(Controller::BUTTON_C, .5, .5);
        m_controller->releaseButton(Controller::BUTTON_Y);
        m_controller->releaseButton(Controller::BUTTON_A);
        m_controller->releaseButton(Controller::BUTTON_B);
        m_reset = true;
    }
}

Nothing::Nothing(GameState *state) : Chain(state)
{
    m_controller = Controller::Instance();
    m_reset = false;
}

Nothing::~Nothing()
{
}
