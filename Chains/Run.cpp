#include <cmath>

#include "Run.h"
void Run::PressButtons()
{
    //Don't run off the edge of the stage
    if(m_state->getStageEdgeGroundPosition() - std::abs(m_state->m_memory->player_two_x) < 30 &&
        (m_isRight == (m_state->m_memory->player_two_x > 0)))
    {
        m_controller->emptyInput();
        return;
    }

    if(!m_isWavedashing)
    {
        switch(m_state->m_memory->player_two_action)
        {
            case WALK_SLOW:
            case DASHING:
            {
                if(m_isRight)
                {
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, 1, .5);
                }
                else
                {
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
                }
                break;
            }
            case WALK_MIDDLE:
            case WALK_FAST:
            {
                //Turning around is fine. We'll dash. But we can't run forward. We need to wavedash
                if(m_state->m_memory->player_two_facing != m_isRight)
                {
                    if(m_isRight)
                    {
                        m_controller->tiltAnalog(Controller::BUTTON_MAIN, 1, .5);
                    }
                    else
                    {
                        m_controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
                    }
                }
                else
                {
                    m_wavedashFrameStart = m_state->m_memory->frame;
                    m_isWavedashing = true;
                    break;
                }
                break;
            }
            case RUNNING:
            {
                //Are we running the wrong way? If so, wavedash back to stop the run
                if(m_state->m_memory->player_two_facing != m_isRight)
                {
                    m_wavedashFrameStart = m_state->m_memory->frame;
                    m_isWavedashing = true;
                    break;
                }
                else
                {
                    if(m_isRight)
                    {
                        m_controller->tiltAnalog(Controller::BUTTON_MAIN, 1, .5);
                    }
                    else
                    {
                        m_controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
                    }
                }
                break;
            }
            default:
            {
                if(m_isRight)
                {
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, 1, .5);
                }
                else
                {
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
                }
                break;
            }
        }
    }

    if(m_isWavedashing)
    {
        uint frame = m_state->m_memory->frame - m_wavedashFrameStart;
        switch(frame)
        {
            case 0:
            {
                //Jump
                m_controller->pressButton(Controller::BUTTON_Y);
                break;
            }
            case 1:
            {
                m_controller->releaseButton(Controller::BUTTON_Y);
                break;
            }
            case 3:
            {
                m_controller->pressButton(Controller::BUTTON_L);
                if(m_isRight)
                {
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, .8, .2);
                }
                else
                {
                    m_controller->tiltAnalog(Controller::BUTTON_MAIN, .2, .2);
                }
                break;
            }
            case 4:
            {
                m_controller->releaseButton(Controller::BUTTON_L);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
                m_isWavedashing = false;
                m_wavedashFrameStart = 0;
                break;
            }
        }
    }
}

//We're always interruptible during a Walk
bool Run::IsInterruptible()
{
    if(m_isWavedashing == true)
    {
        return false;
    }
    return true;
}

Run::Run(bool isRight)
{
    m_isRight = isRight;
    m_isWavedashing = false;
    m_wavedashFrameStart = 0;
}

Run::~Run()
{
}
