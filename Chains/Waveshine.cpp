#include "Waveshine.h"

void Waveshine::PressButtons()
{
    uint frame = m_state->frame - m_startingFrame;
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
            if(m_state->player_one_x > m_state->player_two_x)
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .8, .2);
            }
            else
            {
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .2, .2);
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
    uint frame = m_state->frame - m_startingFrame;
    if(frame >= 11)
    {
        return true;
    }
    return false;
}

Waveshine::Waveshine(GameState *state) : Chain(state)
{
    m_controller = Controller::Instance();
    m_startingFrame = m_state->frame;
}

Waveshine::~Waveshine()
{
}
