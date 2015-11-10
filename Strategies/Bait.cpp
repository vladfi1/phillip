#include <cmath>
#include <iostream>

#include "Bait.h"
#include "../Tactics/CloseDistance.h"
#include "../Tactics/Wait.h"
#include "../Tactics/Parry.h"
#include "../Tactics/ShineCombo.h"

//Returns if the given state allows us to perform any action
bool ReadyForAction(uint a)
{
	switch(a)
	{
		case STANDING:
			return true;
		case WALK_SLOW:
			return true;
		case WALK_MIDDLE:
			return true;
		case WALK_FAST:
			return true;
		case KNEE_BEND:
			return true;
		case CROUCHING:
			return true;
		default:
			return false;
	}
	return false;
}

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
    //If we have a window to upsmash p2, that's preferable
    //std::cout << std::abs(m_state->player_one_x - m_state->player_two_x) << std::endl;

	//If we're not in a state to interupt, just continue with what we've got going
	if((m_tactic != NULL) && (!m_tactic->IsInterruptible()))
	{
		m_tactic->DetermineChain();
		return;
	}

    //If we're able to shine p2 right now, let's do that
    //Are we in range?
    if(std::abs(m_state->player_one_x - m_state->player_two_x) < 11.80)
    {
        //Are we in a state where we can shine?
        if(ReadyForAction(m_state->player_two_action))
        {
            //Is the opponent in a state where they can get hit by shine?
            if(m_state->player_one_action != SHIELD)
            {
                CreateTactic(ShineCombo);
                m_tactic->DetermineChain();
                return;
            }
        }
    }

    //If we need to defend against an attack, that's next priority
    //38.50 is fmash tipper max range
    if(std::abs(m_state->player_one_x - m_state->player_two_x) < 38.50)
    {
        //Don't bother powershielding if the attack is in the wrong direction
        bool player_one_is_to_the_left = (m_state->player_one_x - m_state->player_two_x > 0);
        if(m_state->player_one_facing != player_one_is_to_the_left)
        {
            if(m_state->player_one_action == ACTION::FSMASH_MID)
            {
                CreateTactic(Parry);
                m_tactic->DetermineChain();
                return;
            }
        }
    }

    //If we're not in shine range, get in close
    //TODO: 11.80 is shine range, but the movement algorithm messes up.
    if(std::abs(m_state->player_one_x - m_state->player_two_x) > 21.80)
    {
        CreateTactic(CloseDistance);
        m_tactic->DetermineChain();
        return;
    }
    //If we're in close and p2 is sheilding, just wait
    if(m_state->player_one_action == ACTION::SHIELD)
    {
        CreateTactic(Wait);
        m_tactic->DetermineChain();
        return;
    }
    //TODO: For now, just default to waiting if nothing else fits
    CreateTactic(Wait);
    m_tactic->DetermineChain();
    return;


}
