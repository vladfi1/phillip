#include "EdgeAction.h"

void EdgeAction::PressButtons()
{
    if(m_waitFrames > 0)
    {
        m_waitFrames--;
        m_controller->emptyInput();
        m_readyToInterrupt = false;
        return;
    }

    //Wait until we're not edge catching anymore
    if(m_state->m_memory->player_two_action == EDGE_CATCHING)
    {
        m_controller->emptyInput();
        return;
    }
    if(m_state->m_memory->player_two_action == EDGE_HANGING)
    {
        //Roll up
        if(m_button == Controller::BUTTON_L)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            m_controller->pressButton(Controller::BUTTON_L);
            return;
        }
        //Stand up
        if(m_button == Controller::BUTTON_MAIN)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .70);
            return;
        }
    }
    //Reset the controller afterward
    m_controller->emptyInput();

    if(m_state->m_memory->player_two_action == STANDING)
    {
        m_readyToInterrupt = true;
    }
}

bool EdgeAction::IsInterruptible()
{
    return m_readyToInterrupt;
}

EdgeAction::EdgeAction(Controller::BUTTON button, uint waitFrames)
{
    m_button = button;
    m_readyToInterrupt = false;
    m_waitFrames = waitFrames;
}

EdgeAction::~EdgeAction()
{
}
