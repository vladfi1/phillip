#include "EdgeStall.h"
#include "TransitionHelper.h"

void EdgeStall::PressButtons()
{
    //We're stunned for this duration, so do nothing
    if(m_state->player_two_action == EDGE_CATCHING)
    {
        m_controller->emptyInput();
        return;
    }

    //If we're hanging, then drop down
    if(m_state->player_two_action == EDGE_HANGING)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? 0 : 1, .5);
        return;
    }

    //If we're dropping, shine
    if(m_state->player_two_action == FALLING)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
        m_controller->pressButton(Controller::BUTTON_B);
        return;
    }

    //If we're in shine, jump out
    if(m_state->player_two_action == DOWN_B_AIR)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->pressButton(Controller::BUTTON_Y);
        m_controller->releaseButton(Controller::BUTTON_B);
        return;
    }

    //If jumping upward, then up-b
    if(m_state->player_two_action == JUMPING_ARIAL_FORWARD)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 1);
        m_controller->pressButton(Controller::BUTTON_B);
        return;
    }

    if(m_state->player_two_action == FIREFOX_WAIT_AIR)
    {
        m_controller->emptyInput();
        return;
    }
}

bool EdgeStall::IsInterruptible()
{
    if(m_state->player_two_action == EDGE_HANGING)
    {
        return true;
    }
    if(m_state->frame - m_startingFrame > 60)
    {
        //Safety return. In case we screw something up, don't permanently get stuck in this chain.
        return true;
    }
    return false;
}

EdgeStall::EdgeStall(GameState *state) : Chain(state)
{
    //Quick variable to tell us which edge we're on
    if(m_state->player_one_x > 0)
    {
        m_isLeftEdge = false;
    }
    else
    {
        m_isLeftEdge = true;
    }
    m_startingFrame = m_state->frame;
    m_controller = Controller::Instance();
}

EdgeStall::~EdgeStall()
{
}
