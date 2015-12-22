#include <typeinfo>
#include <math.h>

#include "Juggle.h"
#include "../Constants.h"
#include "../Chains/SmashAttack.h"
#include "../Chains/Nothing.h"
#include "../Chains/Jab.h"

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

    //Calculate distance between players
	double distance = pow(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x, 2);
	distance += pow(m_state->m_memory->player_one_y - m_state->m_memory->player_two_y, 2);
	distance = sqrt(distance);

    bool player_two_is_to_the_left = (m_state->m_memory->player_two_x - m_state->m_memory->player_one_x > 0);
    //If we're in upsmash/jab range, then prepare for attack
    if(distance < FOX_UPSMASH_RANGE && m_state->m_memory->player_two_facing != player_two_is_to_the_left)
    {
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

        int frames_left = m_state->firstHitboxFrame((CHARACTER)m_state->m_memory->player_one_character,
            (ACTION)m_state->m_memory->player_one_action) - m_state->m_memory->player_one_action_frame - 1;

        //Do we have time to upsmash? Do that.
        if(frames_left > 7)
        {
            CreateChain3(SmashAttack, SmashAttack::UP, 0);
            m_chain->PressButtons();
            return;
        }

        //Do we have time to jab? Do that.
        if(frames_left > 3)
        {
            CreateChain(Jab);
            m_chain->PressButtons();
            return;
        }
    }

    //Just do nothing
    CreateChain(Nothing);
    m_chain->PressButtons();
    return;
}
