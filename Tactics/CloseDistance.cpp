#include "CloseDistance.h"
#include "../Chains/Walk.h"

CloseDistance::CloseDistance()
{
    m_chain = NULL;
}

CloseDistance::~CloseDistance()
{
    delete m_chain;
}

void CloseDistance::DetermineChain()
{
    //If opponent is to our right, Walk right
    if(m_state->m_memory->player_one_x > m_state->m_memory->player_two_x)
    {
        CreateChain2(Walk, true);
    }
    //else, Walk left
    else
    {
        CreateChain2(Walk, false);
    }
    m_chain->PressButtons();
}
