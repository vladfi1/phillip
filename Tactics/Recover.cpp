#include <typeinfo>
#include <math.h>
#include <cmath>

#include "Recover.h"
#include "../Constants.h"
#include "../Chains/Nothing.h"
#include "../Chains/EdgeAction.h"
#include "../Chains/EdgeStall.h"
#include "../Chains/FireFox.h"

Recover::Recover()
{
    m_chain = NULL;
}

Recover::~Recover()
{
    delete m_chain;
}

void Recover::DetermineChain()
{
    //If we're not in a state to interupt, just continue with what we've got going
    if((m_chain != NULL) && (!m_chain->IsInterruptible()))
    {
        m_chain->PressButtons();
        return;
    }

    //If we're hanging on the egde, do an edge stall
    if(m_state->m_memory->player_two_action == EDGE_HANGING ||
      m_state->m_memory->player_two_action == EDGE_CATCHING)
    {

        bool isOnRight = m_state->m_memory->player_one_x > 0;
        bool movingRight = m_state->m_memory->player_one_speed_ground_x_self > 0;
        //TODO: made up number 60. Revsit this.
        //Stand up if the enemy is far away, or if they're trying to steal the edge
        if(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x) > 60 ||
          (m_state->m_memory->player_one_action == LANDING_SPECIAL &&
          isOnRight != m_state->m_memory->player_one_facing &&
          movingRight == isOnRight &&
          m_state->getStageEdgeGroundPosition() - std::abs(m_state->m_memory->player_one_x) < 10))
        {
            CreateChain2(EdgeAction, Controller::BUTTON_MAIN);
            m_chain->PressButtons();
            return;
        }

        CreateChain(EdgeStall);
        m_chain->PressButtons();
        return;
    }

    //TODO: This is only rudimentary recovery. Needs to be expanded
    //If we're off the stage...
    if(std::abs(m_state->m_memory->player_two_x) > m_state->getStageEdgeGroundPosition() + .001)
    {
        if(m_state->m_memory->player_two_y > 0 &&
          m_state->m_memory->player_two_y < 10)
        {
            //Side-B back to the stage
        }
        else
        {
            //Firefox back
            CreateChain(FireFox);
            m_chain->PressButtons();
            return;
        }

    }

    //Default to nothing in towards the player
    CreateChain(Nothing);
    m_chain->PressButtons();
    return;
}
