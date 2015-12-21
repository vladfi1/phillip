#include "FullJump.h"

void FullJump::PressButtons()
{
    //If we need to transition, wait until we're at a valid state to be able to jump
    if(m_startingFrame == 0 &&
        (m_state->m_memory->player_two_action == STANDING ||
        m_state->m_memory->player_two_action == WALK_SLOW ||
        m_state->m_memory->player_two_action == WALK_MIDDLE ||
        m_state->m_memory->player_two_action == WALK_FAST ||
        m_state->m_memory->player_two_action == KNEE_BEND ||
        m_state->m_memory->player_two_action == LANDING ||
        m_state->m_memory->player_two_action == EDGE_TEETERING ||
        m_state->m_memory->player_two_action == CROUCHING))
    {
        m_startingFrame = m_state->m_memory->frame;
    }
    if(m_startingFrame == 0)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->releaseButton(Controller::BUTTON_Y);
        m_controller->releaseButton(Controller::BUTTON_B);
        return;
    }

    uint frame = m_state->m_memory->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Jump
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            m_controller->pressButton(Controller::BUTTON_Y);
            break;
        }
        case 6:
        {
            //let go of jump
            m_controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
        case 30:
        {
            //Fastfall
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            break;
        }
        case 31:
        {
            //Fastfall
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            break;
        }
    }
}

//We're always interruptible during a Walk
bool FullJump::IsInterruptible()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 5)
    {
        return true;
    }
    return false;
}

FullJump::FullJump()
{
    //Make sure we are capable of jumping this frame, or else we need to transition
    if(m_state->m_memory->player_two_action == STANDING ||
        m_state->m_memory->player_two_action == WALK_SLOW ||
        m_state->m_memory->player_two_action == WALK_MIDDLE ||
        m_state->m_memory->player_two_action == WALK_FAST ||
        m_state->m_memory->player_two_action == KNEE_BEND ||
        m_state->m_memory->player_two_action == LANDING ||
        m_state->m_memory->player_two_action == EDGE_TEETERING ||
        m_state->m_memory->player_two_action == CROUCHING)
    {
        m_startingFrame = m_state->m_memory->frame;
    }
    else
    {
        m_startingFrame = 0;
    }
}

FullJump::~FullJump()
{
}
