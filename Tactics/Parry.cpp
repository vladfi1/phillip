#include <cmath>
#include <typeinfo>

#include "Parry.h"
#include "../Chains/Powershield.h"
#include "../Chains/SpotDodge.h"

Parry::Parry(GameState *state) : Tactic(state)
{
    m_chain = NULL;
}

Parry::~Parry()
{
    delete m_chain;
}

void Parry::DetermineChain()
{
    if(m_state->player_one_action == ACTION::FSMASH_MID)
    {
        CreateChain(Powershield);
        m_chain->PressButtons();
    }
    else if(m_state->player_one_action == ACTION::GRAB ||
        m_state->player_one_action == ACTION::GRAB_RUNNING)
    {
        CreateChain(SpotDodge);
        m_chain->PressButtons();
    }
}
