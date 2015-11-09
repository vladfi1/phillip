#include <cmath>
#include <iostream>

#include "Bait.h"
#include "../Tactics/CloseDistance.h"
#include "../Tactics/Wait.h"
#include "../Tactics/Parry.h"

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

    //If we're able to shine p2 right now, let's do that

    //If we need to defend against an attack, that's next priority
    //38.50 is fmash tipper max range
    if(std::abs(m_state->player_one_x - m_state->player_two_x) < 38.50)
    {
        if(m_state->player_one_action == ACTION::FSMASH_MID)
        {
            CreateTactic(Parry);
            m_tactic->DetermineChain();
            return;
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
