#include <cmath>

#include "CloseDistance.h"
#include "../Chains/SHDL.h"
#include "../Chains/Multishine.h"

CloseDistance::CloseDistance(GameState *state) : Tactic(state)
{
    m_chain = NULL;
}

CloseDistance::~CloseDistance()
{
    delete m_chain;
}

void CloseDistance::DetermineChain()
{
    //If we're far away, laser
    if(std::abs(m_state->player_one_x - m_state->player_two_x) > 40)
    {
        delete m_chain;
        m_chain = new SHDL(m_state);
    }
    //else, multishine
    else
    {
        delete m_chain;
        m_chain = new Multishine(m_state);
    }
    m_chain->PressButtons();
}
