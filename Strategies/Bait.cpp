#include "Bait.h"
#include "../Tactics/CloseDistance.h"

Bait::Bait(GameState *state) : Strategy(state)
{
    m_tactic = NULL;
}

Bait::~Bait()
{
    delete m_tactic;
}

void Bait::DetermineTactic()
{
    //TODO support more than just CloseDistance
    if(m_tactic == NULL)
    {
        m_tactic = new CloseDistance(m_state);

    }
    m_tactic->DetermineChain();
}
