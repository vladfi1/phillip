#include <cmath>
#include <math.h>

#include "Sandbag.h"
#include "../Constants.h"
#include "../Tactics/CloseDistance.h"
#include "../Tactics/CreateDistance.h"
#include "../Tactics/Wait.h"
#include "../Tactics/Parry.h"
#include "../Tactics/Recover.h"
#include "../Tactics/ShowOff.h"

Sandbag::Sandbag()
{
    m_tactic = NULL;
    m_attackFrame = 0;
    m_lastAction = (ACTION)m_state->m_memory->player_one_action;
    m_shieldedAttack = false;
    m_actionChanged = true;
    m_chargingLastFrame = false;
    m_lastActionCount = 0;
}

Sandbag::~Sandbag()
{
    delete m_tactic;
}

void Sandbag::DetermineTactic()
{
    //TODO: Move this logic away from here and Bait into KillOpponent
    //Determine how many frames of lag our opponent has during the LANDING_SPECIAL action
    // Unfortunately, the game reuses LANDING_SPECIAL for both landing from an UP-B and from a wavedash
    // So it's non-trivial to figure out which it is.
    if(m_state->m_memory->player_one_action == LANDING_SPECIAL)
    {
        if(m_lastAction == DEAD_FALL || m_lastAction == UP_B)
        {
            m_state->setLandingState(true);
        }
        if(m_lastAction == AIRDODGE)
        {
            m_state->setLandingState(false);
        }
    }

    //Has opponent just released a sharged smash attack?
    bool m_chargedSmashReleased = false;
    if(!m_state->m_memory->player_one_charging_smash && m_chargingLastFrame)
    {
        m_chargedSmashReleased = true;
    }
    m_chargingLastFrame = m_state->m_memory->player_one_charging_smash;

    //So, turns out that the game changes the player's action state (to 2 or 3) on us when they're charging
    //If this happens, just change it back. Maybe there's a more elegant solution
    if(m_state->m_memory->player_one_action == 0x02 ||
        m_state->m_memory->player_one_action == 0x03)
    {
        m_state->m_memory->player_one_action = m_lastAction;
    }

    //Update the attack frame if the enemy started a new action
    if((m_lastAction != (ACTION)m_state->m_memory->player_one_action) ||
        (m_state->m_memory->player_one_action_counter > m_lastActionCount) ||
        (m_state->m_memory->player_one_action_frame == 0))
    {
        m_lastActionCount = m_state->m_memory->player_one_action_counter;
        m_shieldedAttack = false;
        m_actionChanged = true;
        m_lastAction = (ACTION)m_state->m_memory->player_one_action;
        if(m_state->isAttacking((ACTION)m_state->m_memory->player_one_action))
        {
            m_attackFrame = m_state->m_memory->frame;
        }
    }
    //Continuing same previous action
    else
    {
        m_actionChanged = false;
        if(m_state->m_memory->player_two_action == SHIELD_STUN ||
            m_state->m_memory->player_two_action == SPOTDODGE ||
            m_state->m_memory->player_two_action == EDGE_GETUP_QUICK ||
            m_state->m_memory->player_two_action == EDGE_GETUP_SLOW)
        {
            m_shieldedAttack = true;
        }
    }
    if(!m_state->isAttacking((ACTION)m_state->m_memory->player_one_action))
    {
        m_attackFrame = 0;
    }

    //If we're not in a state to interupt, just continue with what we've got going
    if((m_tactic != NULL) && (!m_tactic->IsInterruptible()))
    {
        m_tactic->DetermineChain();
        return;
    }

    //If we're still warping in at the start of the match or in shield stun, then just hang out and do nothing
    if(m_state->m_memory->player_two_action == ENTRY ||
        m_state->m_memory->player_two_action == ENTRY_START ||
        m_state->m_memory->player_two_action == ENTRY_END ||
        m_state->m_memory->player_two_action == SHIELD_STUN ||
        m_state->m_memory->player_two_action == LANDING_SPECIAL)
    {
        CreateTactic(Wait);
        m_tactic->DetermineChain();
        return;
    }

    //Calculate distance between players
    double distance = pow(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x, 2);
    distance += pow(m_state->m_memory->player_one_y - m_state->m_memory->player_two_y, 2);
    distance = sqrt(distance);

    //If we're hanging on the egde, and the oponnent is on the stage area, then recover
    if((m_state->m_memory->player_two_action == EDGE_HANGING ||
        m_state->m_memory->player_two_action == EDGE_CATCHING) &&
        std::abs(m_state->m_memory->player_one_x) < m_state->getStageEdgeGroundPosition() + .001 &&
        m_state->m_memory->player_one_y > -5)
    {
        CreateTactic(Recover);
        m_tactic->DetermineChain();
        return;
    }

    //If we just shielded a downtilt and they're still in the attack, get out of there
    if(m_state->m_memory->player_two_action == SHIELD_RELEASE &&
        m_state->m_memory->player_one_action == DOWNTILT)
    {
        CreateTactic(CreateDistance);
        m_tactic->DetermineChain();
        return;
    }

    //If the enemy is in a looping attack outside our range, back off
    if(distance > 35 &&
        distance < 60 &&
        (m_state->m_memory->player_one_action == DOWNTILT ||
        m_state->m_memory->player_one_action == NEUTRAL_ATTACK_1 ||
        m_state->m_memory->player_one_action == NEUTRAL_ATTACK_2))
    {
        CreateTactic(CreateDistance);
        m_tactic->DetermineChain();
        return;
    }

    //If we need to defend against an attack, that's next priority. Unless we've already shielded this attack
    if(!m_shieldedAttack && distance < MARTH_FSMASH_RANGE)
    {
        //Don't bother parrying if the attack is over
        if(m_state->lastHitboxFrame((CHARACTER)m_state->m_memory->player_one_character, (ACTION)m_state->m_memory->player_one_action) >=
            m_state->m_memory->player_one_action_frame)
        {
            //Don't bother parrying if the attack is in the wrong direction
            bool player_one_is_to_the_left = (m_state->m_memory->player_one_x - m_state->m_memory->player_two_x > 0);
            if((m_state->m_memory->player_one_facing != player_one_is_to_the_left || (m_state->isReverseHit((ACTION)m_state->m_memory->player_one_action))) &&
                (m_state->m_memory->player_two_on_ground ||
                m_state->m_memory->player_two_action == EDGE_HANGING ||
                m_state->m_memory->player_two_action == EDGE_CATCHING))
            {
                if(m_state->isAttacking((ACTION)m_state->m_memory->player_one_action))
                {
                    //If the p1 action changed, scrap the old Parry and make a new one.
                    if(m_actionChanged || m_chargedSmashReleased)
                    {
                        delete m_tactic;
                        m_tactic = NULL;
                    }

                    CreateTactic(Parry);
                    m_tactic->DetermineChain();
                    return;
                }
            }
        }
    }

    //If the enemy is dead, then celebrate!
    if(m_state->m_memory->player_one_y < MARTH_LOWER_EVENT_HORIZON ||
        (m_state->m_memory->player_one_action >= DEAD_DOWN &&
        m_state->m_memory->player_one_action <= DEAD_FLY_SPLATTER_FLAT) ||
        (m_state->m_memory->player_one_action == DEAD_FALL &&
         m_state->m_memory->player_one_y < -20))
    {
        //Have to be on the ground or on edge
        if(m_state->m_memory->player_two_on_ground ||
            m_state->m_memory->player_two_action == EDGE_HANGING ||
            m_state->m_memory->player_two_action == EDGE_CATCHING)
        {
            CreateTactic(ShowOff);
            m_tactic->DetermineChain();
            return;
        }
    }

    //If we're off the stage and don't need to edgeguard, get back on
    if(std::abs(m_state->m_memory->player_two_x) > m_state->getStageEdgeGroundPosition() + .001)
    {
        CreateTactic(Recover);
        m_tactic->DetermineChain();
        return;
    }

    //If we're not in shine range, get in close
    if(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x) > FOX_SHINE_RADIUS)
    {
        CreateTactic(CloseDistance);
        m_tactic->DetermineChain();
        return;
    }
    //If we're in close and p2 is sheilding, just wait
    if(m_state->m_memory->player_one_action == SHIELD)
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
