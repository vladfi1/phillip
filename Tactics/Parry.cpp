#include <cmath>
#include <typeinfo>

#include "Parry.h"
#include "../Chains/Powershield.h"
#include "../Chains/SpotDodge.h"
#include "../Chains/EdgeAction.h"

Parry::Parry()
{
    m_chain = NULL;
}

Parry::~Parry()
{
    delete m_chain;
}

void Parry::DetermineChain()
{
    if(m_state->m_memory->player_two_action == EDGE_HANGING)
    {
        CreateChain2(EdgeAction, Controller::BUTTON_MAIN);
        m_chain->PressButtons();
        return;
    }

    //TODO: SWORD_DANCE_4_LOW is a multi-hit attack. Let's handle that differently. Maybe just light shield
    if(m_state->m_memory->player_one_action == ACTION::GRAB ||
        m_state->m_memory->player_one_action == ACTION::GRAB_RUNNING)
    {
        CreateChain(SpotDodge);
        m_chain->PressButtons();
    }
    //We're assuming there's no other grab-type attacks. (Yoshi's neutral-b for instance)
    else
    {
        CreateChain(Powershield);
        m_chain->PressButtons();
    }
}
