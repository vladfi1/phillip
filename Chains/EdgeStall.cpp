#include "EdgeStall.h"
#include "TransitionHelper.h"

void EdgeStall::PressButtons()
{
    //We're stunned for this duration, so do nothing
    if(m_state->m_memory->player_two_action == EDGE_CATCHING)
    {
        m_catchCount++;
        if(m_catchCount == 7)
        {
            m_catchCount = 0;
            m_pressedBack = true;
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? 0 : 1, .5);
            return;
        }
        else
        {
            m_controller->emptyInput();
            return;
        }
    }

    //If we're hanging, then drop down
    if(m_state->m_memory->player_two_action == EDGE_HANGING)
    {
        if(m_pressedBack)
        {
            m_controller->emptyInput();
            m_pressedBack = false;
            return;
        }
        else
        {
          m_pressedBack = true;
          m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? 0 : 1, .5);
          return;
        }
    }

    //Firefox
    if(m_state->m_memory->player_two_action == FALLING)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 1);
        m_controller->pressButton(Controller::BUTTON_B);
        return;
    }

    if(m_state->m_memory->player_two_action == FIREFOX_WAIT_AIR)
    {
        m_controller->emptyInput();
        return;
    }
}

bool EdgeStall::IsInterruptible()
{
    if(m_state->m_memory->player_two_action == EDGE_HANGING ||
      m_state->m_memory->player_two_action == EDGE_CATCHING)
    {
        return true;
    }
    if(m_state->m_memory->frame - m_startingFrame > 30)
    {
        //Safety return. In case we screw something up, don't permanently get stuck in this chain.
        return true;
    }
    return false;
}

EdgeStall::EdgeStall()
{
    //Quick variable to tell us which edge we're on
    if(m_state->m_memory->player_one_x > 0)
    {
        m_isLeftEdge = false;
    }
    else
    {
        m_isLeftEdge = true;
    }
    m_startingFrame = m_state->m_memory->frame;
    m_pressedBack = false;
    m_catchCount = 0;
}

EdgeStall::~EdgeStall()
{
}
