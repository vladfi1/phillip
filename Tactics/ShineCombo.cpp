#include <cmath>
#include <typeinfo>

#include "ShineCombo.h"
#include "../Chains/ShineUpsmash.h"

ShineCombo::ShineCombo(GameState *state) : Tactic(state)
{
    m_chain = NULL;
}

ShineCombo::~ShineCombo()
{
    delete m_chain;
}

void ShineCombo::DetermineChain()
{
    CreateChain(ShineUpsmash);
    m_chain->PressButtons();
}
