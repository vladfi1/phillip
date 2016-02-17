#include "KillOpponent.h"
#include "../Strategies/Bait.h"
#include "../Strategies/Sandbag.h"

KillOpponent::KillOpponent()
{
    m_strategy = NULL;
}

KillOpponent::~KillOpponent()
{
    delete m_strategy;
}

void KillOpponent::Strategize()
{
    //If the opponent is invincible, don't attack them. Just dodge everything they do
    if(m_state->m_memory->player_one_invulnerable)
    {
        CreateStrategy(Sandbag);
        m_strategy->DetermineTactic();
    }
    else
    {
        CreateStrategy(Bait);
        m_strategy->DetermineTactic();
    }

}
