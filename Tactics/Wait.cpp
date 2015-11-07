#include <cmath>

#include "Wait.h"
#include "../Chains/Nothing.h"

Wait::Wait(GameState *state) : Tactic(state)
{
    m_chain = NULL;
}

Wait::~Wait()
{
    delete m_chain;
}

void Wait::DetermineChain()
{
    delete m_chain;
    m_chain = new Nothing(m_state);
    m_chain->PressButtons();
}
