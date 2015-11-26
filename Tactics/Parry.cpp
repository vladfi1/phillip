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
    //TODO: SWORD_DANCE_4_LOW is a multi-hit attack. Let's handle that differently. Maybe just light shield
    if(m_state->player_one_action == ACTION::GRAB ||
        m_state->player_one_action == ACTION::GRAB_RUNNING)
    {
        CreateChain2(SpotDodge, m_startFrame);
    }
    //We're assuming there's no other grab-type attacks. (Yoshi's neutral-b for instance)
    else
    {
        CreateChain2(Powershield, m_startFrame);
    }
    m_chain->PressButtons();
}
