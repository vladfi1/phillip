#include <cmath>

#include "GrabEdge.h"

void GrabEdge::PressButtons()
{
    //If we're far away from the edge, then walk at the edge
    //XXX: We're not dashing for now, because that got complicated
    if(std::abs(m_state->player_two_x) < 72.5656)
    {
        m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? .25 : .75, .5);
        return;
    }

    //If we're within 13 units from the edge (on the stage) then crouch, wavedash back
    if(std::abs(m_state->player_two_x) > 72.5656 && std::abs(m_state->player_two_x) < 85.5656)
    {
        if(!m_isInWavedash)
        {
            m_isInWavedash = true;
            m_startingFrame = m_state->frame;
        }

        uint frame = m_state->frame - m_startingFrame;
        switch(frame)
        {
            case 0:
            {
                //Turn around (technically, this dashes)
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? 1 : 0, .5);
                break;
            }
            //Wavedash back
            case 2:
            {
                //Jump
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
                m_controller->pressButton(Controller::BUTTON_Y);
                break;
            }
            case 3:
            {
                m_controller->releaseButton(Controller::BUTTON_Y);
                break;
            }
            case 5:
            {
                //Airdodge backwards to the edge
                m_controller->pressButton(Controller::BUTTON_L);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, m_isLeftEdge ? .2 : .8, .2);
                break;
            }
            case 6:
            {
                m_controller->releaseButton(Controller::BUTTON_L);
                m_controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
                break;
            }
            //TODO: fastfall to the edge
        }
        return;
    }
}

bool GrabEdge::IsInterruptible()
{
    if(!m_isInWavedash)
    {
        return true;
    }

    uint frame = m_state->frame - m_startingFrame;
    if(frame >= 15)
    {
        return true;
    }
    return false;
}

GrabEdge::GrabEdge(GameState *state) : Chain(state)
{
    //Quick variable to tell us which edge to grab
    if(m_state->player_one_x > 0)
    {
        m_isLeftEdge = false;
    }
    else
    {
        m_isLeftEdge = true;
    }
    m_startingFrame = 0;
    m_controller = Controller::Instance();
    m_isInWavedash = false;
}

GrabEdge::~GrabEdge()
{
}
