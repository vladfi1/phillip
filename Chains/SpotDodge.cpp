#include "SpotDodge.h"

void SpotDodge::PressButtons()
{
    //If we need to transition, wait until we're at a valid state to be able to dodge
    if(m_startingFrame == 0 &&
        (m_state->player_two_action == STANDING ||
        m_state->player_two_action == WALK_SLOW ||
        m_state->player_two_action == WALK_MIDDLE ||
        m_state->player_two_action == WALK_FAST ||
        m_state->player_two_action == KNEE_BEND ||
        m_state->player_two_action == LANDING ||
        m_state->player_two_action == EDGE_TEETERING ||
        m_state->player_two_action == CROUCHING))
    {
        m_startingFrame = m_state->frame;
    }
    if(m_startingFrame == 0)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->releaseButton(Controller::BUTTON_L);
        return;
    }

    uint frame = m_state->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Spot dodge
            m_controller->pressButton(Controller::BUTTON_L);
            break;
        }
        case 1:
        {
            //down
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            break;
        }
        case 2:
        {
            //let go
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            m_controller->releaseButton(Controller::BUTTON_L);
            break;
        }
    }
}

//We're always interruptible during a jog
bool SpotDodge::IsInterruptible()
{
    uint frame = m_state->frame - m_startingFrame;
    if(frame >= 23)
    {
        return true;
    }
    return false;
}

SpotDodge::SpotDodge(GameState *state) : Chain(state)
{
    //Make sure we are capable of dodging this frame, or else we need to transition
    if(m_state->player_two_action == STANDING ||
        m_state->player_two_action == WALK_SLOW ||
        m_state->player_two_action == WALK_MIDDLE ||
        m_state->player_two_action == WALK_FAST ||
        m_state->player_two_action == KNEE_BEND ||
        m_state->player_two_action == LANDING ||
        m_state->player_two_action == EDGE_TEETERING ||
        m_state->player_two_action == CROUCHING)
    {
        m_startingFrame = m_state->frame;
    }
    else
    {
        m_startingFrame = 0;
    }
    m_controller = Controller::Instance();
}

SpotDodge::~SpotDodge()
{
}
