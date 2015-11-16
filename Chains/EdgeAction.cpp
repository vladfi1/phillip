#include "EdgeAction.h"

void EdgeAction::PressButtons()
{
    //Wait until we're not edge catching anymore
    if(m_state->player_two_action == EDGE_CATCHING)
    {
        return;
    }
    if(m_state->player_two_action == EDGE_HANGING)
    {
        //Roll up
        if(m_button == Controller::BUTTON_L)
        {
            m_controller->pressButton(Controller::BUTTON_L);
            return;
        }
    }
    //Reset the controller afterward
    m_controller->releaseButton(Controller::BUTTON_L);
    m_controller->releaseButton(Controller::BUTTON_A);
    m_controller->releaseButton(Controller::BUTTON_Y);
    m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);

    if(m_state->player_two_action == STANDING)
    {
        m_readyToInterrupt = true;
    }
}

bool EdgeAction::IsInterruptible()
{
    return m_readyToInterrupt;
}

EdgeAction::EdgeAction(GameState *state, Controller::BUTTON button) : Chain(state)
{
    m_button = button;
    m_controller = Controller::Instance();
    m_readyToInterrupt = false;
}

EdgeAction::~EdgeAction()
{
}
