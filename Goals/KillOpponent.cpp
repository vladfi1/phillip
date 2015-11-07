#include "KillOpponent.h"
#include "../Strategies/Bait.h"

KillOpponent::KillOpponent(GameState *state) : Goal(state)
{
    m_strategy = NULL;
}

KillOpponent::~KillOpponent()
{
    //TODO: We're only supporting Bait for now. Eventually make this configurable
    delete m_strategy;
}

void KillOpponent::Strategize()
{
    if(m_strategy == NULL)
    {
        //TODO: We're only supporting Bait for now. Eventually make this configurable
        m_strategy = new Bait(m_state);
    }
    m_strategy->DetermineTactic();
}
