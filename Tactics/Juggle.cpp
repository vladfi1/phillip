#include <typeinfo>

#include "Juggle.h"
#include "../Chains/SmashAttack.h"

Juggle::Juggle(GameState *state) : Tactic(state)
{
    m_chain = NULL;
}

Juggle::~Juggle()
{
    delete m_chain;
}

void Juggle::DetermineChain()
{
    //TODO: For now, just upsmash once

    if(m_chain != NULL && m_chain->IsInterruptible())
    {
        delete m_chain;
        m_chain = new SmashAttack(m_state, SmashAttack::UP);
    }
    CreateChain2(SmashAttack, SmashAttack::UP);
    m_chain->PressButtons();
}
