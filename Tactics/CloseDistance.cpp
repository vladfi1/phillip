#include <cmath>
#include <typeinfo>

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
        CreateChain2(Jog, true);
    }
    //else, jog left
    else
    {
        CreateChain2(Jog, false);
    }
    m_chain->PressButtons();

}
