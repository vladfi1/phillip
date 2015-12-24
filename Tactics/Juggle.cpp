#include <typeinfo>
#include <math.h>
#include <cmath>

#include "Juggle.h"
#include "../Constants.h"
#include "../Chains/SmashAttack.h"
#include "../Chains/Nothing.h"
#include "../Chains/Jab.h"
#include "../Chains/Run.h"

Juggle::Juggle()
{
    m_roll_position = 0;
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

    //If they're rolling, go punish it where they will stop
    if(m_state->m_memory->player_one_action == ROLL_FORWARD ||
        m_state->m_memory->player_one_action == ROLL_BACKWARD ||
        m_state->m_memory->player_one_action == EDGE_ROLL_SLOW ||
        m_state->m_memory->player_one_action == EDGE_ROLL_QUICK)
    {
        //Figure out where they will stop rolling, only on the first frame
        if(m_state->m_memory->player_one_action_frame == 1)
        {
            if(m_state->m_memory->player_one_action == ROLL_FORWARD)
            {
                if(m_state->m_memory->player_one_facing)
                {
                    m_roll_position = m_state->m_memory->player_one_x + MARTH_ROLL_DISTANCE;
                }
                else
                {
                    m_roll_position = m_state->m_memory->player_one_x - MARTH_ROLL_DISTANCE;
                }
            }
            else if(m_state->m_memory->player_one_action == ROLL_BACKWARD)
            {
                if(m_state->m_memory->player_one_facing)
                {
                    m_roll_position = m_state->m_memory->player_one_x - MARTH_ROLL_DISTANCE;
                }
                else
                {
                    m_roll_position = m_state->m_memory->player_one_x + MARTH_ROLL_DISTANCE;
                }
            }
            else if(m_state->m_memory->player_one_action == EDGE_ROLL_SLOW ||
                m_state->m_memory->player_one_action == EDGE_ROLL_QUICK)
            {

                if(m_state->m_memory->player_one_facing)
                {
                    m_roll_position = m_state->m_memory->player_one_x + MARTH_EDGE_ROLL_DISTANCE;
                }
                else
                {
                    m_roll_position = m_state->m_memory->player_one_x - MARTH_EDGE_ROLL_DISTANCE;
                }
            }
            if(m_roll_position > m_state->getStageEdgeGroundPosition())
            {
                m_roll_position = m_state->getStageEdgeGroundPosition();
            }
            else if (m_roll_position < (-1) * m_state->getStageEdgeGroundPosition())
            {
                m_roll_position = (-1) * m_state->getStageEdgeGroundPosition();
            }
        }

        int frames_left;
        if(m_state->m_memory->player_one_action == ROLL_FORWARD ||
            m_state->m_memory->player_one_action == ROLL_BACKWARD)
        {
            frames_left = MARTH_ROLL_FRAMES - m_state->m_memory->player_one_action_frame;
        }
        else if(m_state->m_memory->player_one_action == EDGE_ROLL_SLOW)
        {
            frames_left = MARTH_EDGE_ROLL_FRAMES - m_state->m_memory->player_one_action_frame;
        }
        else if(m_state->m_memory->player_one_action == EDGE_ROLL_QUICK)
        {
            frames_left = MARTH_EDGE_ROLL_SLOW_FRAMES - m_state->m_memory->player_one_action_frame;
        }

        if(frames_left <= 7)
        {
            CreateChain(Nothing);
            m_chain->PressButtons();
            return;
        }

        //Upsmash if we're in range and facing the right way
        //  Factor in sliding during the smash animation
        double distance;
        if(m_state->m_memory->player_two_action == DASHING ||
            m_state->m_memory->player_two_action == RUNNING)
        {
            distance = std::abs(std::abs(m_roll_position - m_state->m_memory->player_two_x) - 8);
        }
        else
        {
            distance = std::abs(m_roll_position - m_state->m_memory->player_two_x);
        }


        bool to_the_left = m_roll_position > m_state->m_memory->player_two_x;
        if(distance < FOX_UPSMASH_RANGE_NEAR &&
            to_the_left == m_state->m_memory->player_two_facing)
        {
            CreateChain3(SmashAttack, SmashAttack::UP, frames_left - 10);
            m_chain->PressButtons();
            return;
        }
        else
        {
            CreateChain2(Run, to_the_left);
            m_chain->PressButtons();
            return;
        }
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
