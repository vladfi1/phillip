#include "Jog.h"

void Jog::PressButtons()
{
    if(m_isRight)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .75, .5);
    }
    else
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .25, .5);
    }
}

Jog::Jog(GameState *state, bool isRight) : Chain(state)
{
    m_controller = Controller::Instance();
    m_isRight = isRight;
}

Jog::~Jog()
{
}
