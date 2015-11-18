#include <cmath>

#include "SHDL.h"

void SHDL::PressButtons()
{
    //If we need to transition, wait until we're at a valid state
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
        //If we're too close to the edge, it's not safe to jump. Move inwards for just a frame
        if((m_state->player_two_x) > 85.5206985474)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .25, .5);
            return;
        }
        if((m_state->player_two_x) < -85.5206985474)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .75, .5);
            return;
        }
        //If we're ready, but facing the wrong direction, then turn around.
        if(m_state->player_two_facing == (m_state->player_one_x < m_state->player_two_x))
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_state->player_two_facing ? .25 : .75, .5);
            return;
        }
        else
        {
            m_startingFrame = m_state->frame;
        }
    }
    if(m_startingFrame == 0)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->releaseButton(Controller::BUTTON_Y);
        m_controller->releaseButton(Controller::BUTTON_B);
        return;
    }

    uint frame = m_state->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Jump
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
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
    //We're interuptible if we haven't really started yet
    if(m_startingFrame == 0)
    {
        return true;
    }

    uint frame = m_state->frame - m_startingFrame;
    if(frame >= 27)
    {
        return true;
    }
    return false;
}

SHDL::SHDL(GameState *state) : Chain(state)
{
    //Make sure we are capable of jumping this frame, or else we need to transition
    if(m_state->player_two_action == STANDING ||
        m_state->player_two_action == WALK_SLOW ||
        m_state->player_two_action == WALK_MIDDLE ||
        m_state->player_two_action == WALK_FAST ||
        m_state->player_two_action == KNEE_BEND ||
        m_state->player_two_action == LANDING ||
        m_state->player_two_action == EDGE_TEETERING ||
        m_state->player_two_action == CROUCHING)
    {
        //If we're too close to the edge, it's not safe to jump. Move inwards for just a frame
        if(std::abs(m_state->player_two_x) > 70)
        {
            m_startingFrame = 0;

        }
        //If we're otherwise in a ready state, but facing the wrong direction, then turn around.
        else if(m_state->player_two_facing == (m_state->player_one_x < m_state->player_two_x))
        {
            m_startingFrame = 0;
        }
        else
        {
            m_startingFrame = m_state->frame;
        }
    }
    else
    {
        m_startingFrame = 0;
    }
    m_controller = Controller::Instance();
}

SHDL::~SHDL()
{
}
