#include <cmath>

#include "Waveshine.h"

void Waveshine::PressButtons()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            //Shine
            m_controller->pressButton(Controller::BUTTON_B);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            break;
        }
        case 6:
        {
            //Let go of down b
            m_controller->releaseButton(Controller::BUTTON_B);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            //Jump out of our shine
            m_controller->pressButton(Controller::BUTTON_Y);
            break;
        }
        case 7:
        {
            m_controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
        case 9:
        {
            m_controller->pressButton(Controller::BUTTON_L);
            //TODO: still assumes we're facing the opponent
            //If we're close to the edge, don't wavedash off
            if(std::abs(m_state->m_memory->player_two_x) + 5 > m_state->getStageEdgeGroundPosition())
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .2);
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
            break;
        }
        case 10:
        {
            m_controller->releaseButton(Controller::BUTTON_L);
            m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            break;
        }
    }
}

bool Waveshine::IsInterruptible()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 11)
    {
        return true;
    }
    return false;
}

Waveshine::Waveshine()
{
    m_startingFrame = m_state->m_memory->frame;
}

Waveshine::~Waveshine()
{
}
