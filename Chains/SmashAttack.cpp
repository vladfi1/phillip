#include "SmashAttack.h"

void SmashAttack::PressButtons()
{
    uint frame = m_state->frame - m_startingFrame;
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
    uint frame = m_state->frame - m_startingFrame;
    if(frame >= 41)
    {
        return true;
    }
    return false;}

SmashAttack::SmashAttack(GameState *state, DIRECTION d) : Chain(state)
{
    m_direction = d;
    m_controller = Controller::Instance();
    //TODO: Work on transitions to this chain
    m_startingFrame = m_state->frame;
}

SmashAttack::~SmashAttack()
{
}
