#include <cmath>

#include "SHDL.h"
#include "TransitionHelper.h"

void SHDL::PressButtons()
{
    if(m_action != m_state->m_memory->player_two_action)
    {
        m_action = (ACTION)m_state->m_memory->player_two_action;
        if(m_action == LANDING)
        {
            m_landedFrame = m_state->m_memory->frame;
        }
    }

    //Get setup for the SHDL
    if(m_startingFrame == 0)
    {
        //If we're too close to the edge, it's not safe to jump. Move inwards for just a frame
        if((m_state->m_memory->player_two_x) > m_state->getStageEdgeGroundPosition() - 3)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .25, .5);
            return;
        }
        if((m_state->m_memory->player_two_x ) < (((int)m_state->getStageEdgeGroundPosition()) * -1) + 3)
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .75, .5);
            return;
        }
        //If we're ready, but facing the wrong direction, then turn around.
        if(m_state->m_memory->player_two_facing == (m_state->m_memory->player_one_x < m_state->m_memory->player_two_x))
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_state->m_memory->player_two_facing ? .25 : .75, .5);
            return;
        }
        else
        {
            //Let's start lasering!
            m_startingFrame = m_state->m_memory->frame;
        }
    }

    //If we've started the SHDL
    if(m_startingFrame > 0)
    {
        //If we're waiting for landing lag to end, just wait. Else, let's jump
        if(m_state->m_memory->player_two_on_ground &&
            m_state->m_memory->player_two_action != KNEE_BEND)
        {
            if(m_state->m_memory->frame >= m_landedFrame + 3)
            {
                if(m_jumpedFrame > 0)
                {
                    //If we get here, then we tried to jump and failed. So let go of jump and try again
                    m_jumpedFrame = 0;
                    m_controller->emptyInput();
                    return;
                }
                m_jumpedFrame = m_state->m_memory->frame;
                m_controller->pressButton(Controller::BUTTON_Y);
                return;
            }
            else
            {
                m_controller->emptyInput();
                return;
            }
        }

        //Let go of jump once we started
        if(m_state->m_memory->player_two_action == KNEE_BEND)
        {
            m_controller->releaseButton(Controller::BUTTON_Y);
            return;
        }

        //Alternate pressing and releasing B
        if(m_holdingLaser)
        {
            m_controller->releaseButton(Controller::BUTTON_B);
            m_holdingLaser = !m_holdingLaser;
            return;

        }
        else
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            m_controller->pressButton(Controller::BUTTON_B);
            m_holdingLaser = !m_holdingLaser;
            return;
        }

        m_controller->emptyInput();
        return;
    }
}

bool SHDL::IsInterruptible()
{
    //We're interuptible if we haven't really started yet
    if(m_startingFrame == 0)
    {
        return true;
    }

    if(TransitionHelper::canJump((ACTION)m_state->m_memory->player_two_action) &&
        (m_landedFrame > 0) &&
        (m_state->m_memory->frame > m_landedFrame + 20))
    {
        return true;
    }

    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 60)
    {
        //Emergency backup kill for the chain in case we get stuck here somehow
        return true;
    }
    return false;
}

SHDL::SHDL()
{
    m_holdingLaser = false;
    m_startingFrame = 0;
    m_landedFrame = 0;
    m_jumpedFrame = 0;
    m_action = (ACTION)m_state->m_memory->player_two_action;
    //If we start landing, then assume we need to wait for the landing lag to finish
    if(m_action == LANDING)
    {
        m_landedFrame = m_state->m_memory->frame;
    }
}

SHDL::~SHDL()
{
}
