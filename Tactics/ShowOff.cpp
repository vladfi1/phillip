#include <cmath>

#include "ShowOff.h"
#include "../Chains/Multishine.h"
#include "../Chains/EdgeAction.h"
#include "../Chains/Nothing.h"
#include "../Chains/Wavedash.h"
#include "../Chains/Walk.h"

ShowOff::ShowOff()
{
    m_chain = NULL;
}

ShowOff::~ShowOff()
{
    delete m_chain;
}

void ShowOff::DetermineChain()
{
    //If we're not in a state to interupt, just continue with what we've got going
    if((m_chain != NULL) && (!m_chain->IsInterruptible()))
    {
        m_chain->PressButtons();
        return;
    }
    else
    {
        //If we get here, make a whole new chain, don't continue an old one
        delete m_chain;
        m_chain = NULL;
    }

    if(m_state->getStageEdgeGroundPosition() - std::abs(m_state->m_memory->player_two_x) < 5)
    {
        CreateChain2(Walk, m_state->m_memory->player_two_x < 0);
        m_chain->PressButtons();
        return;
    }

    if(m_state->m_memory->player_two_action == EDGE_HANGING ||
        m_state->m_memory->player_two_action == EDGE_CATCHING)
    {
        CreateChain2(EdgeAction, Controller::BUTTON_MAIN);
        m_chain->PressButtons();
        return;
    }

    bool isOnRight = m_state->m_memory->player_one_x < m_state->m_memory->player_two_x;
    if(m_state->m_memory->player_one_action == ON_HALO_DESCENT)
    {
        CreateChain2(Wavedash, !isOnRight);
        m_chain->PressButtons();
        return;
    }

    if(m_state->m_memory->player_two_on_ground)
    {
        CreateChain(Multishine);
        m_chain->PressButtons();
        return;
    }

    //Fall back to doing nothing
    CreateChain(Nothing);
    m_chain->PressButtons();
    return;
}
