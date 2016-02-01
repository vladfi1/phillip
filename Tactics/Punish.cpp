#include <typeinfo>
#include <math.h>
#include <cmath>

#include "Punish.h"
#include "../Constants.h"
#include "../Chains/SmashAttack.h"
#include "../Chains/Nothing.h"
#include "../Chains/Jab.h"
#include "../Chains/Run.h"
#include "../Chains/Walk.h"
#include "../Chains/Wavedash.h"
#include "../Chains/EdgeAction.h"

#include <iostream>

Punish::Punish()
{
    m_roll_position = 0;
    m_chain = NULL;
}

Punish::~Punish()
{
    delete m_chain;
}

void Punish::DetermineChain()
{
    //If we're not in a state to interupt, just continue with what we've got going
    if((m_chain != NULL) && (!m_chain->IsInterruptible()))
    {
        m_chain->PressButtons();
        return;
    }

    if(m_state->m_memory->player_one_action == SPOTDODGE)
    {
        CreateChain(Nothing);
        m_chain->PressButtons();
        return;
    }

    //If we're hanging on the egde, and they are falling above the stage, stand up
    if(m_state->m_memory->player_one_action == DEAD_FALL &&
        m_state->m_memory->player_two_action == EDGE_HANGING &&
        std::abs(m_state->m_memory->player_one_x) < m_state->getStageEdgeGroundPosition() + .001)
    {
        CreateChain2(EdgeAction, Controller::BUTTON_MAIN);
        m_chain->PressButtons();
        return;
    }

    //If they're rolling, go punish it where they will stop
    if(m_state->m_memory->player_one_action == ROLL_FORWARD ||
        m_state->m_memory->player_one_action == ROLL_BACKWARD ||
        m_state->m_memory->player_one_action == EDGE_ROLL_SLOW ||
        m_state->m_memory->player_one_action == EDGE_ROLL_QUICK ||
        m_state->m_memory->player_one_action == EDGE_GETUP_QUICK ||
        m_state->m_memory->player_one_action == EDGE_GETUP_SLOW)
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
            else if(m_state->m_memory->player_one_action == EDGE_GETUP_QUICK ||
                m_state->m_memory->player_one_action == EDGE_GETUP_SLOW)
            {

                if(m_state->m_memory->player_one_facing)
                {
                    m_roll_position = m_state->m_memory->player_one_x + MARTH_GETUP_DISTANCE;
                }
                else
                {
                    m_roll_position = m_state->m_memory->player_one_x - MARTH_GETUP_DISTANCE;
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
            frames_left = MARTH_EDGE_ROLL_SLOW_FRAMES - m_state->m_memory->player_one_action_frame;
        }
        else if(m_state->m_memory->player_one_action == EDGE_ROLL_QUICK)
        {
            frames_left = MARTH_EDGE_ROLL_FRAMES - m_state->m_memory->player_one_action_frame;
        }
        else if(m_state->m_memory->player_one_action == EDGE_GETUP_QUICK)
        {
            frames_left = MARTH_EDGE_GETUP_QUICK_FRAMES - m_state->m_memory->player_one_action_frame;
        }
        else if(m_state->m_memory->player_one_action == EDGE_GETUP_SLOW)
        {
            frames_left = MARTH_EDGE_GETUP_SLOW_FRAMES - m_state->m_memory->player_one_action_frame;
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
            double slidingAdjustment = 12.25 * (std::abs(m_state->m_memory->player_two_speed_ground_x_self));
            distance = std::abs(std::abs(m_roll_position - m_state->m_memory->player_two_x) - slidingAdjustment);
        }
        else
        {
            distance = std::abs(m_roll_position - m_state->m_memory->player_two_x);
        }

        bool to_the_left = m_roll_position > m_state->m_memory->player_two_x;
        if(distance < FOX_UPSMASH_RANGE_NEAR &&
            to_the_left == m_state->m_memory->player_two_facing)
        {
            CreateChain3(SmashAttack, SmashAttack::UP, std::max(0, frames_left - 9));
            m_chain->PressButtons();
            return;
        }
        else
        {
            //If the target location is right behind us, just turn around, don't run
            if(distance < FOX_UPSMASH_RANGE_NEAR &&
                to_the_left != m_state->m_memory->player_two_facing)
            {
                CreateChain2(Walk, to_the_left);
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
    }

    //Calculate distance between players
    double distance = pow(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x, 2);
    distance += pow(m_state->m_memory->player_one_y - m_state->m_memory->player_two_y, 2);
    distance = sqrt(distance);

    //How many frames do we have until we need to do something?
    int frames_left;
    //Are we before the attack or after?
    if(m_state->m_memory->player_one_action_frame < m_state->lastHitboxFrame((CHARACTER)m_state->m_memory->player_one_character,
        (ACTION)m_state->m_memory->player_one_action))
    {
        //Before
        frames_left = m_state->firstHitboxFrame((CHARACTER)m_state->m_memory->player_one_character,
            (ACTION)m_state->m_memory->player_one_action) - m_state->m_memory->player_one_action_frame - 1;
    }
    else
    {
        //After
        frames_left = m_state->totalActionFrames((CHARACTER)m_state->m_memory->player_one_character,
           (ACTION)m_state->m_memory->player_one_action) - m_state->m_memory->player_one_action_frame - 1;
    }

    bool player_two_is_to_the_left = (m_state->m_memory->player_one_x > m_state->m_memory->player_two_x);
    //If we're in upsmash/jab range, then prepare for attack
    if(m_state->m_memory->player_two_facing == player_two_is_to_the_left && //Facing the right way?
        (distance < FOX_UPSMASH_RANGE ||
        (distance < FOX_UPSMASH_RANGE - 25.5 && (m_state->m_memory->player_two_action == DASHING ||
            m_state->m_memory->player_two_action == RUNNING))))
    {
        //Do we have time to upsmash? Do that.
        if(frames_left > 7)
        {
            //Do two less frames of charging than we could, just to be safe
            CreateChain3(SmashAttack, SmashAttack::UP, std::max(0, frames_left - 9));
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

    //Is it safe to wavedash in after shielding the attack?
    //  Don't wavedash off the edge of the stage
    if(frames_left > 14 &&
        m_state->m_memory->player_two_action == SHIELD_RELEASE &&
        (m_state->getStageEdgeGroundPosition() > std::abs(m_state->m_memory->player_two_x) + 10))
    {
        CreateChain2(Wavedash, player_two_is_to_the_left);
        m_chain->PressButtons();
        return;
    }

    //Default to walking in towards the player
    CreateChain2(Walk, player_two_is_to_the_left);
    m_chain->PressButtons();
    return;
}
