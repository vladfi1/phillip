#include <cmath>

#include "CloseDistance.h"
#include "../Chains/Jog.h"

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


    //If opponent is to our right, jog right
    if(m_state->player_one_x > m_state->player_two_x)
    {
        delete m_chain;
        m_chain = new Jog(m_state, true);
    }
    //else, multishine
    else
    {
        delete m_chain;
        m_chain = new Jog(m_state, false);

    }
    m_chain->PressButtons();

}
