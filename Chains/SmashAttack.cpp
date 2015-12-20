#include "SmashAttack.h"

void SmashAttack::PressButtons()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    switch(frame)
    {
        case 0:
        {
            switch(m_direction)
            {
                case LEFT:
                {
                    m_controller->tiltAnalog(Controller::BUTTON_C, 0, .5);
                    break;
                }
                case RIGHT:
                {
                    m_controller->tiltAnalog(Controller::BUTTON_C, 1, .5);
                    break;
                }
                case UP:
                {
                    m_controller->tiltAnalog(Controller::BUTTON_C, .5, 1);
                    break;
                }
                case DOWN:
                {
                    m_controller->tiltAnalog(Controller::BUTTON_C, .5, 0);
                    break;
                }
            }
            break;
        }
        case 1:
        {
            m_controller->tiltAnalog(Controller::BUTTON_C, .5, .5);
            break;
        }
    }
}

bool SmashAttack::IsInterruptible()
{
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 41)
    {
        return true;
    }
    return false;}

SmashAttack::SmashAttack(DIRECTION d)
{
    m_direction = d;
    //TODO: Work on transitions to this chain
    m_startingFrame = m_state->m_memory->frame;
}

SmashAttack::~SmashAttack()
{
}
