#include <cmath>

#include "Waveshine.h"

void Waveshine::PressButtons()
{
    //Do nothing if we're in hitlag
    if(m_state->m_memory->player_two_hitlag_frames_left > 0)
    {
        if(m_hitlagFrames == 0)
        {
            m_hitlagFrames = m_state->m_memory->player_two_hitlag_frames_left;
        }
        m_controller->emptyInput();
        return;
    }

    if(m_frameShined == 0)
    {
        //Shine
        m_isBusy = true;
        m_frameShined = m_state->m_memory->frame;
        m_controller->pressButton(Controller::BUTTON_B);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
        return;
    }

    if(m_state->m_memory->frame == m_frameShined+m_hitlagFrames+1)
    {
        //Let go of down b
        m_controller->releaseButton(Controller::BUTTON_B);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        return;
    }

    if(m_state->m_memory->frame == m_frameShined+m_hitlagFrames+4)
    {
        //Jump out of our shine
        m_frameJumped = m_state->m_memory->frame;
        m_controller->pressButton(Controller::BUTTON_Y);
        return;
    }

    if(m_state->m_memory->frame == m_frameShined+m_hitlagFrames+5)
    {
        m_controller->releaseButton(Controller::BUTTON_Y);
        return;
    }

    if(m_state->m_memory->player_two_action == KNEE_BEND &&
        m_frameKneeBend == 0)
    {
        m_frameKneeBend = m_state->m_memory->frame;
        return;
    }

    if(m_state->m_memory->frame == m_frameKneeBend+1)
    {
        m_controller->pressButton(Controller::BUTTON_L);
        //TODO: still assumes we're facing the opponent
        //If we're close to the edge, don't wavedash off
        if(std::abs(m_state->m_memory->player_two_x) + 2 > m_state->getStageEdgeGroundPosition())
        {
            //If we're super duper close the the edge, we HAVE to wavedash back, or die
            if(m_state->m_memory->player_two_x > 0)
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .2, .2);
            }
            else
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .8, .2);
            }
        }
        else if(std::abs(m_state->m_memory->player_two_x) + 10 > m_state->getStageEdgeGroundPosition())
        {
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
        }
        else
        {
            if(m_state->m_memory->player_one_x > m_state->m_memory->player_two_x)
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .8, .2);
            }
            else
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .2, .2);
            }
        }
        return;
    }

    if(m_state->m_memory->frame == m_frameKneeBend+2)
    {
        m_isBusy = false;
        m_controller->releaseButton(Controller::BUTTON_L);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        return;
    }
}

bool Waveshine::IsInterruptible()
{
    if(m_state->m_memory->frame - m_startingFrame > 20)
    {
        return true;
    }
    return !m_isBusy;
}

Waveshine::Waveshine()
{
    m_startingFrame = m_state->m_memory->frame;
    m_frameJumped = 0;
    m_frameShined = 0;
    m_hitlagFrames = 0;
    m_frameKneeBend = 0;
    m_isBusy = false;
}

Waveshine::~Waveshine()
{
}
