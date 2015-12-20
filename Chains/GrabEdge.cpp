#include <cmath>

#include "GrabEdge.h"
#include "TransitionHelper.h"

void GrabEdge::PressButtons()
{
    if(m_isInFastfall)
    {
        m_controller->emptyInput();
        return;
    }

    //If we're far away from the edge, then walk at the edge
    //XXX: We're not dashing for now, because that got complicated
    if(!m_isInWavedash && (std::abs(m_state->m_memory->player_two_x) < 72.5656))
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? .25 : .75, .5);
        return;
    }

    //We need to be able to dash, so let's transition to crouching, where we can definitely dash
    if(!m_isInWavedash && !TransitionHelper::canDash((ACTION)m_state->m_memory->player_two_action))
    {
        TransitionHelper::Transition((ACTION)m_state->m_memory->player_two_action, CROUCHING);
        return;
    }

    m_isInWavedash = true;

    //Fastfall once in the air
    if((m_state->m_memory->player_two_action == FALLING) && !m_isInFastfall)
    {
        m_isInFastfall = true;
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
        return;
    }

    //Dash Backwards
    if(m_state->m_memory->player_two_action == CROUCHING ||
        m_state->m_memory->player_two_action == STANDING ||
        m_state->m_memory->player_two_action == TURNING ||
        m_state->m_memory->player_two_action == EDGE_TEETERING_START ||
        m_state->m_memory->player_two_action == EDGE_TEETERING)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? 1 : 0, .5);
        return;
    }

    //Once we're dashing, jump
    if(m_state->m_memory->player_two_action == DASHING)
    {
        //Jump TODO: backwards jump
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
        m_controller->pressButton(Controller::BUTTON_Y);
        return;
    }

    //Just hang out and do nothing while knee bending
    if(m_state->m_memory->player_two_action == KNEE_BEND)
    {
        m_controller->emptyInput();
        return;
    }

    //Once we're in the air, airdodge backwards to the edge
    if(!m_state->m_memory->player_two_on_ground && m_isInWavedash)
    {
        m_controller->pressButton(Controller::BUTTON_L);
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? .2 : .8, .2);
        return;
    }

    //Just hang out and do nothing while wave landing
    if(m_state->m_memory->player_two_action == LANDING_SPECIAL)
    {
        m_controller->emptyInput();
        return;
    }

    m_controller->emptyInput();
}

bool GrabEdge::IsInterruptible()
{
    if(!m_isInWavedash)
    {
        return true;
    }
    if(m_state->m_memory->player_two_action == EDGE_HANGING)
    {
        return true;
    }
    //Don't permanently get stuck here
    uint frame = m_state->m_memory->frame - m_startingFrame;
    if(frame > 60)
    {
        return true;
    }
    return false;
}

GrabEdge::GrabEdge()
{
    //Quick variable to tell us which edge to grab
    if(m_state->m_memory->player_one_x > 0)
    {
        m_isLeftEdge = false;
    }
    else
    {
        m_isLeftEdge = true;
    }
    m_startingFrame = m_state->m_memory->frame;
    m_isInWavedash = false;
    m_isInFastfall = false;
}

GrabEdge::~GrabEdge()
{
}
