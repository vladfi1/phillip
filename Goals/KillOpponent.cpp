#include "KillOpponent.h"
#include "../Strategies/Bait.h"

KillOpponent::KillOpponent(GameState *state) : Goal(state)
{
    m_strategy = NULL;
}

KillOpponent::~KillOpponent()
{
    delete m_strategy;
}

void KillOpponent::Strategize()
{
    //If the enemy is off the stage, let's edgeguard them
    CreateStrategy(Bait);
    m_strategy->DetermineTactic();
}
