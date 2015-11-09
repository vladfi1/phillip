#include <cmath>
#include <typeinfo>

#include "Parry.h"
#include "../Chains/Powershield.h"

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
    CreateChain(Powershield);
    m_chain->PressButtons();
}
