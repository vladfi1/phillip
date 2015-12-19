#include <cmath>

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
        m_controller->emptyInput();
        return;
    }

    //If we're medium range or more, and reversefacing, don't bother doing anything.
    float distance = std::abs(m_state->player_one_x - m_state->player_two_x);
    if(m_isReverseFacing && (distance > 18))
    {
        m_controller->emptyInput();
        return;
    }

    uint frame = m_state->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Spot dodge
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
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

SpotDodge::SpotDodge(GameState *state, uint startFrame) : Chain(state)
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
    bool player_one_is_to_the_left = (m_state->player_one_x - m_state->player_two_x > 0);
    if(m_state->player_one_facing != player_one_is_to_the_left)
    {
        m_isReverseFacing = false;
    }
    else
    {
        m_isReverseFacing = true;
    }
    m_startFrame = startFrame;
    m_controller = Controller::Instance();
}

SpotDodge::~SpotDodge()
{
}
