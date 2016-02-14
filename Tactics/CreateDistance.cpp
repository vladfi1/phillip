#include <cmath>

#include "../Chains/ShortHopLaser.h"
#include "../Chains/Wavedash.h"
#include "../Chains/Nothing.h"

#include "CreateDistance.h"

CreateDistance::CreateDistance()
{
    m_chain = NULL;
}

CreateDistance::~CreateDistance()
{
    delete m_chain;
}

void CreateDistance::DetermineChain()
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

    bool isOnRight = m_state->m_memory->player_one_x < m_state->m_memory->player_two_x;
    if(m_state->m_memory->player_two_action == SHIELD_RELEASE)
    {
        CreateChain2(Wavedash, isOnRight);
        m_chain->PressButtons();
        return;
    }

    double distance = std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x);

    //If we're right on the edge of range, and are walkign inwards, just wavedash back
    if(distance < 45 &&
        (m_state->m_memory->player_two_action == WALK_SLOW ||
        m_state->m_memory->player_two_action == WALK_MIDDLE ||
        m_state->m_memory->player_two_action == WALK_FAST))
    {
        CreateChain2(Wavedash, isOnRight);
        m_chain->PressButtons();
        return;
    }

    if(m_state->getStageEdgeGroundPosition() - std::abs(m_state->m_memory->player_two_x) < 40)
    {
        CreateChain(Nothing);
        m_chain->PressButtons();
    }
    else
    {
        CreateChain2(ShortHopLaser, RETREATING);
        m_chain->PressButtons();
    }

}
