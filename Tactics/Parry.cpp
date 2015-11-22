#include <cmath>
#include <typeinfo>

#include "Parry.h"
#include "../Chains/Powershield.h"
#include "../Chains/SpotDodge.h"

Parry::Parry(GameState *state, uint startFrame) : Tactic(state)
{
    m_chain = NULL;
    m_startFrame = startFrame;
}

Parry::~Parry()
{
    delete m_chain;
}

void Parry::DetermineChain()
{
    if(m_state->player_one_action == ACTION::FSMASH_MID)
    {
        CreateChain2(Powershield, m_startFrame);
    }
    else if(m_state->player_one_action == ACTION::GRAB ||
        m_state->player_one_action == ACTION::GRAB_RUNNING)
    {
        CreateChain2(SpotDodge, m_startFrame);
    }
    m_chain->PressButtons();
}
