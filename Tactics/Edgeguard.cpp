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
#include "../Chains/MarthKiller.h"
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

    double lowerEventHorizon = MARTH_LOWER_EVENT_HORIZON;
    if(m_state->m_memory->player_one_jumps_left == 0)
    {
        lowerEventHorizon += MARTH_DOUBLE_JUMP_HEIGHT;
    }

    //Marth is dead if he's at this point
    if(m_state->m_memory->player_one_y < lowerEventHorizon)
    {
        if(m_state->m_memory->player_two_action == EDGE_HANGING)
        {
            CreateChain2(EdgeAction, Controller::BUTTON_MAIN);
            m_chain->PressButtons();
            return;
        }
        if(m_state->m_memory->player_two_on_ground)
        {
            CreateChain(Nothing);
            m_chain->PressButtons();
            return;
        }
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
        std::abs(m_state->m_memory->player_two_x) < m_state->getStageEdgeGroundPosition())
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

        double edge_distance_x = std::abs(std::abs(m_state->m_memory->player_one_x) - m_state->getStageEdgePosition());
        double edge_distance_y = std::abs(m_state->m_memory->player_one_y - EDGE_HANGING_Y_POSITION);

        //If marth is out of attack range and UP-B range, then go ahead and do it
        //TODO: Added some hardcoded wiggle room to be safe
        if(distance > MARTH_FSMASH_RANGE &&
            (edge_distance_x > MARTH_UP_B_X_DISTANCE + 5 ||
            edge_distance_y > MARTH_UP_B_HEIGHT + 5))
        {
            CreateChain(GrabEdge);
            m_chain->PressButtons();
            return;
        }

        //If marth is side-B'ing (out of attack range) then it's safe
        if(m_state->m_memory->player_one_action == SWORD_DANCE_1)
        {
            CreateChain(GrabEdge);
            m_chain->PressButtons();
            return;
        }
    }

    //Edgehog our opponent if they're UP-B'ing sweetspotted.
    //Grab the edge if we're still on the stage
    if(m_state->m_memory->player_one_action == UP_B &&
        m_state->m_memory->player_two_action == EDGE_HANGING)
    {
        //Is marth so low that he must grab the edge? If so, just roll up.
        if(m_state->m_memory->player_one_y < MARTH_RECOVER_HIGH_EVENT_HORIZON + MARTH_DOUBLE_JUMP_HEIGHT)
        {
            CreateChain3(EdgeAction, Controller::BUTTON_L, 2);
            m_chain->PressButtons();
            return;
        }
        //If not, he might land on the stage. So, just stand up and attack on the other end
        else
        {
            CreateChain2(EdgeAction, Controller::BUTTON_MAIN);
            m_chain->PressButtons();
            return;
        }
    }

    double jumpOnlyEventHorizon = MARTH_JUMP_ONLY_EVENT_HORIZON;
    if(m_state->m_memory->player_one_jumps_left == 0 &&
        m_state->m_memory->player_one_action != JUMPING_ARIAL_FORWARD &&
        m_state->m_memory->player_one_action != JUMPING_ARIAL_BACKWARD)
    {
        jumpOnlyEventHorizon += MARTH_DOUBLE_JUMP_HEIGHT;
    }

    //Do the marth killer if we're on the stage and Marth must up-b to recover
    if(m_state->m_memory->player_two_on_ground &&
        m_state->m_memory->player_one_y < jumpOnlyEventHorizon &&
        m_state->m_memory->player_one_y > lowerEventHorizon)
    {
        CreateChain(MarthKiller);
        m_chain->PressButtons();
        return;
    }

    //Just hang out and do nothing
    CreateChain(Nothing);
    m_chain->PressButtons();
    return;
}
