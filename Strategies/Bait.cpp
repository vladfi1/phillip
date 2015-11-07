#include <cmath>

#include "Bait.h"
#include "../Tactics/CloseDistance.h"
#include "../Tactics/Wait.h"

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

    //If we're far away, get in close
    if(std::abs(m_state->player_one_x - m_state->player_two_x) > 10)
    {
        delete m_tactic;
        m_tactic = new CloseDistance(m_state);
    }
    //If we're in close, just wait
    else
    {
        delete m_tactic;
        m_tactic = new Wait(m_state);
    }
    m_tactic->DetermineChain();

}
