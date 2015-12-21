#include <typeinfo>

#include "Juggle.h"
#include "../Chains/SmashAttack.h"
#include "../Chains/Nothing.h"

Juggle::Juggle()
{
    m_chain = NULL;
}

Juggle::~Juggle()
{
    delete m_chain;
}

void Juggle::DetermineChain()
{
    //If we're not in a state to interupt, just continue with what we've got going
    if((m_chain != NULL) && (!m_chain->IsInterruptible()))
    {
        m_chain->PressButtons();
        return;
    }

    //Spot dodge
    if(m_state->m_memory->player_one_action == SPOTDODGE &&
        m_state->m_memory->player_one_action_frame < 18)
    {
        CreateChain3(SmashAttack, SmashAttack::UP, 18 - m_state->m_memory->player_one_action_frame);
        m_chain->PressButtons();
        return;
    }

    //Marth counter
    if((m_state->m_memory->player_one_action == MARTH_COUNTER ||
        m_state->m_memory->player_one_action == MARTH_COUNTER_FALLING) &&
        m_state->m_memory->player_one_action_frame < 50)
    {
        CreateChain3(SmashAttack, SmashAttack::UP, 50 - m_state->m_memory->player_one_action_frame);
        m_chain->PressButtons();
        return;
    }

    //Just do nothing
    CreateChain(Nothing);
    m_chain->PressButtons();
    return;
}
