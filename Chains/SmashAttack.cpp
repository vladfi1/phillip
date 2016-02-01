#include "SmashAttack.h"

void SmashAttack::PressButtons()
{
    //Jump-cancel the smash
    if(m_state->m_memory->player_two_action == RUNNING ||
        m_state->m_memory->player_two_action == DASHING ||
        m_state->m_memory->player_two_action == SHIELD ||
        m_state->m_memory->player_two_action == SHIELD_RELEASE)
    {
        m_canInterrupt = false;
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 1);
        m_controller->releaseButton(Controller::BUTTON_A);
        return;
    }

    uint frame = m_state->m_memory->frame - m_startingFrame;
    //TODO The charge point changes for different smashes
    if(frame == 1 || frame == 0 || m_state->m_memory->player_two_action == KNEE_BEND)
    {
        m_canInterrupt = false;
        m_controller->releaseButton(Controller::BUTTON_Y);
        switch(m_direction)
        {
            case LEFT:
            {
                m_controller->pressButton(Controller::BUTTON_A);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
                break;
            }
            case RIGHT:
            {
                m_controller->pressButton(Controller::BUTTON_A);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, 1, .5);
                break;
            }
            case UP:
            {
                m_controller->pressButton(Controller::BUTTON_A);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 1);
                break;
            }
            case DOWN:
            {
                m_controller->pressButton(Controller::BUTTON_A);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
                break;
            }
        }
        return;
    }

    //Charge the attack...
    if(m_charge_frames > 0)
    {
        m_charge_frames--;
        //Just keep previous input
        return;
    }
    else
    {
        m_canInterrupt = true;
        m_controller->releaseButton(Controller::BUTTON_A);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
    }
}

bool SmashAttack::IsInterruptible()
{
    if(m_canInterrupt)
    {
        return true;
    }

    //Emergency backup case to make sure we don't get stuck here
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame >= 90)
    {
        return true;
    }
    return false;
}

SmashAttack::SmashAttack(DIRECTION d, uint charge_frames)
{
    m_direction = d;
    m_startingFrame = m_state->m_memory->frame;
    m_charge_frames = charge_frames;
    m_canInterrupt = true;
}

SmashAttack::~SmashAttack()
{
}
