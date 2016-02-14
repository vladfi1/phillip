#include <cmath>
#include <algorithm>

#include "MarthKiller.h"
void MarthKiller::PressButtons()
{
    //Are we already in position to do a MarthKiller?
    if(m_state->getStageEdgeGroundPosition() - std::abs(m_state->m_memory->player_two_x) < 2 &&
        m_state->m_memory->player_two_facing != m_onRight)
    {
        m_rolled = true;
        if(m_state->m_memory->player_two_action == SHIELD)
        {
            m_shielded = true;
        }
    }

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

    //Let go of hard shield, start light shield
    if(m_state->m_memory->frame >= m_rollFrame+1 &&
        m_rollFrame > 0)
    {
        m_controller->releaseButton(Controller::BUTTON_L);
        m_controller->tiltAnalog(Controller::BUTTON_L, .4);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_onRight ? .9 : .1, .5);
        return;
    }

    //If we are ready to shield but never needed to roll, then just go ahead with the light shield
    // Incrementally hold further to the side to avoid rolling
    if(m_rollFrame == 0)
    {
        m_controller->releaseButton(Controller::BUTTON_L);
        m_controller->tiltAnalog(Controller::BUTTON_L, .4);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_onRight ? .5 + m_shieldOffset : .5 - m_shieldOffset, .5);
        //Increment by .05 each frame, up to the max of .5
        m_shieldOffset += .02;
        m_shieldOffset = std::min((double)m_shieldOffset, .5);
        return;
    }

    //If all else fails, just hang out and do nothing
    m_controller->emptyInput();
    return;
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
    m_rollFrame = 0;
    m_shieldOffset = 0;
}

MarthKiller::~MarthKiller()
{
}
