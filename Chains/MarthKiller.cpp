#include <cmath>

#include "MarthKiller.h"

void MarthKiller::PressButtons()
{
    if(m_shielded == false)
    {
        m_controller->pressButton(Controller::BUTTON_L);
        m_shielded = true;
        return;
    }

    //Roll over to the edge
    if(m_rolled == false)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_onRight ? 1 : 0, .5);
        m_rolled = true;
        m_rollFrame = m_state->m_memory->frame;
        return;
    }

    //Let go of hard shield, start light shield diagonally
    if(m_state->m_memory->frame == m_rollFrame+1)
    {
        m_controller->releaseButton(Controller::BUTTON_L);
        m_controller->tiltAnalog(Controller::BUTTON_L, .4);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_onRight ? .9 : .1, .2);
        return;
    }

    if(!m_state->m_memory->player_two_on_ground)
    {
        m_controller->emptyInput();
        return;
    }

    if(m_state->m_memory->player_two_action == EDGE_CATCHING)
    {
        m_controller->emptyInput();
        return;
    }
}

bool MarthKiller::IsInterruptible()
{
    if(m_state->m_memory->player_two_action == EDGE_HANGING ||
        m_state->m_memory->player_one_action == EDGE_HANGING ||
        m_state->m_memory->player_one_action == EDGE_CATCHING ||
        m_state->m_memory->player_one_on_ground)
    {
        m_controller->tiltAnalog(Controller::BUTTON_L, 0);
        return true;
    }

    if(m_state->m_memory->player_one_action == DEAD_FALL &&
        m_state->m_memory->player_one_y < -23)
    {
        m_controller->tiltAnalog(Controller::BUTTON_L, 0);
        return true;
    }

    //Get unstuck eventually. Shouldn't get here.
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame > 180)
    {
        m_controller->tiltAnalog(Controller::BUTTON_L, 0);
        return true;
    }
    return false;
}

MarthKiller::MarthKiller()
{
    m_rolled = false;
    m_shielded = false;
    m_onRight = m_state->m_memory->player_two_x > 0;
    m_startingFrame = m_state->m_memory->frame;
}

MarthKiller::~MarthKiller()
{
}
