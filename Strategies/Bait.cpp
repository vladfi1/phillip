#include <cmath>
#include <math.h>
#include <iostream>

#include "Bait.h"
#include "../Constants.h"
#include "../Tactics/CloseDistance.h"
#include "../Tactics/Wait.h"
#include "../Tactics/Parry.h"
#include "../Tactics/ShineCombo.h"
#include "../Tactics/Laser.h"
#include "../Tactics/Edgeguard.h"
#include "../Tactics/Juggle.h"

Bait::Bait(GameState *state) : Strategy(state)
{
    m_tactic = NULL;
    m_attackFrame = 0;
    m_lastAction = (ACTION)m_state->player_one_action;
    m_shieldedAttack = false;
}

Bait::~Bait()
{
    delete m_tactic;
}

void Bait::DetermineTactic()
{
    //std::cout << std::abs(m_state->player_one_x - m_state->player_two_x) << std::endl;
    //std::cout << "state: " << m_state->player_one_action << std::endl;

    //Update the attack frame if the enemy started a new action
    if(m_lastAction != (ACTION)m_state->player_one_action)
    {
        m_shieldedAttack = false;
        m_lastAction = (ACTION)m_state->player_one_action;
        if(isAttacking((ACTION)m_state->player_one_action))
        {
            m_attackFrame = m_state->frame;
        }
    }
    //Continuing same previous action
    else
    {
        if(m_state->player_one_action == SHIELD_STUN)
        {
            m_shieldedAttack = true;
        }
    }
    if(!isAttacking((ACTION)m_state->player_one_action))
    {
        m_attackFrame = 0;
    }

	//If we're not in a state to interupt, just continue with what we've got going
	if((m_tactic != NULL) && (!m_tactic->IsInterruptible()))
	{
		m_tactic->DetermineChain();
		return;
	}

	//distance formula
	double distance = pow(std::abs(m_state->player_one_x - m_state->player_two_x), 2);
	distance += pow(std::abs(m_state->player_one_y - m_state->player_two_y), 2);
	distance = sqrt(distance);

    //If we're able to shine p2 right now, let's do that
    if(std::abs(distance) < FOX_SHINE_RADIUS)
    {
        //Are we in a state where we can shine?
        if(ReadyForAction(m_state->player_two_action))
        {
            //Is the opponent in a state where they can get hit by shine?
            if(m_state->player_one_action != SHIELD &&
                m_state->player_one_action != MARTH_COUNTER &&
                m_state->player_one_action != MARTH_COUNTER_FALLING &&
                m_state->player_one_action != EDGE_CATCHING)
            {
                CreateTactic(ShineCombo);
                m_tactic->DetermineChain();
                return;
            }
        }
    }

    //If we need to defend against an attack, that's next priority. Unless we've already shielded this attack
    if(!m_shieldedAttack && std::abs(m_state->player_one_x - m_state->player_two_x) < MARTH_FSMASH_RANGE)
    {
        //Don't bother parrying if the attack is in the wrong direction
		//TODO: Maybe sometime worry about reverse hits. But probably not? (this should only trigger at mid range)
        bool player_one_is_to_the_left = (m_state->player_one_x - m_state->player_two_x > 0);
        if(m_state->player_one_facing != player_one_is_to_the_left)
        {
            if(m_state->player_one_action == ACTION::FSMASH_MID ||
				m_state->player_one_action == ACTION::GRAB ||
				m_state->player_one_action == ACTION::GRAB_RUNNING)
            {
                CreateTactic2(Parry, m_attackFrame);
                m_tactic->DetermineChain();
                return;
            }
        }
    }

	//If we're far away, just laser
	if(std::abs(m_state->player_one_x - m_state->player_two_x) > 90)
	{
        CreateTactic(Laser);
        m_tactic->DetermineChain();
        return;
    }

    //If the opponent is off the stage, let's edgeguard them
    //NOTE: Sometimes players can get a little below 0 in Y coordinates without being off the stage
    if(std::abs(m_state->player_one_x) > 88.4735 || m_state->player_one_y < -5.5)
    {
        CreateTactic(Edgeguard);
        m_tactic->DetermineChain();
        return;
    }

    //If we're not in shine range, get in close
    if(std::abs(m_state->player_one_x - m_state->player_two_x) > FOX_SHINE_RADIUS)
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

bool Bait::isAttacking(ACTION action)
{
    switch(action)
    {
        case FSMASH_MID:
        {
            return true;
        }
        case GRAB:
        {
            return true;
        }
        case GRAB_RUNNING:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}
