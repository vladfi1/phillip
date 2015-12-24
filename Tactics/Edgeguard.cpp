#include <cmath>
#include <math.h>

#include "Edgeguard.h"
#include "../Constants.h"
#include "../Chains/Nothing.h"
#include "../Chains/EdgeStall.h"
#include "../Chains/JumpCanceledShine.h"
#include "../Chains/GrabEdge.h"
#include "../Chains/EdgeAction.h"
#include "../Chains/Walk.h"
#include "../Controller.h"

Edgeguard::Edgeguard()
{
    m_chain = NULL;
}

Edgeguard::~Edgeguard()
{
    delete m_chain;
}

void Edgeguard::DetermineChain()
{
	//If we're not in a state to interupt, just continue with what we've got going
	if((m_chain != NULL) && (!m_chain->IsInterruptible()))
	{
		m_chain->PressButtons();
		return;
	}

	//distance formula
	double distance = pow(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x), 2);
	distance += pow(std::abs(m_state->m_memory->player_one_y - m_state->m_memory->player_two_y), 2);
	distance = sqrt(distance);

    //If we're able to shine p1 right now, let's do that
    if(std::abs(distance) < FOX_SHINE_RADIUS)
    {
        //Are we in a state where we can shine?
        if(m_state->m_memory->player_two_action == FALLING)
        {
            //Is the opponent in a state where they can get hit by shine?
            if(!m_state->m_memory->player_one_invulnerable)
            {
                CreateChain(JumpCanceledShine);
                m_chain->PressButtons();
                return;
            }
        }
    }

    //If the opponent is hanging on the edge, walk up the the edge
    if((m_state->m_memory->player_one_action == SLIDING_OFF_EDGE ||
        m_state->m_memory->player_one_action == EDGE_CATCHING ||
        m_state->m_memory->player_one_action == EDGE_HANGING) &&
        m_state->m_memory->player_two_on_ground &&
        std::abs(m_state->m_memory->player_two_x) < m_state->getStageEdgePosition() - 10)
    {
        if(m_state->m_memory->player_two_x > 0)
        {
            CreateChain2(Walk, true);
            m_chain->PressButtons();
            return;
        }
        else
        {
            CreateChain2(Walk, false);
            m_chain->PressButtons();
            return;
        }
    }

    //If we're still on the stage, see if it's safe to grab the edge
    if(m_state->m_memory->player_two_on_ground)
    {
        //If the enemy is in a stunned damage state, go ahead and try.
        //TODO: This is not really that great of a heuristic. But let's go with it for now
        if(m_state->isDamageState((ACTION)m_state->m_memory->player_one_action))
        {
            CreateChain(GrabEdge);
            m_chain->PressButtons();
            return;
        }

        //Calculate distance between players
    	double distance = pow(std::abs(m_state->m_memory->player_one_x) - m_state->getStageEdgePosition(), 2);
    	distance += pow(m_state->m_memory->player_one_y, 2);
    	distance = sqrt(distance);

        //If marth is out of attack range, then go ahead and do it
        if(distance > MARTH_FSMASH_RANGE)
        {
            CreateChain(GrabEdge);
            m_chain->PressButtons();
            return;
        }
    }

    //Edgehog our opponent if they're UP-B'ing sweetspotted.
    //Grab the edge if we're still on the stage
    if(m_state->m_memory->player_one_y < 50 && m_state->m_memory->player_one_action == UP_B)
    {
        CreateChain2(EdgeAction, Controller::BUTTON_L);
        m_chain->PressButtons();
        return;
    }

    //Edgestall to kill time
    if(m_state->m_memory->player_two_action == EDGE_CATCHING ||
        m_state->m_memory->player_two_action == EDGE_HANGING)
    {
        CreateChain(EdgeStall);
        m_chain->PressButtons();
        return;
    }

    //Just hang out and do nothing
    CreateChain(Nothing);
    m_chain->PressButtons();
    return;
}
