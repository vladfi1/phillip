#include "TransitionHelper.h"
#include "../Controller.h"

void TransitionHelper::Transition(ACTION from, ACTION to)
{
    Controller *controller = Controller::Instance();

    switch(to)
    {
        case STANDING:
        {
            controller->emptyInput();
        }
        case CROUCHING:
        {
            controller->emptyInput();
        }
        case DASHING:
        {
            if(from == RUNNING)
            {
                controller->tiltAnalog(Controller::BUTTON_MAIN, .5, 0);
            }
            else
            {
                controller->emptyInput();
            }
        }
        default:
        {
            controller->emptyInput();
        }
    }
}

bool TransitionHelper::canJump(ACTION action)
{
    switch(action)
    {
        case STANDING:
        {
            return true;
        }
        case WALK_SLOW:
        {
            return true;
        }
        case WALK_MIDDLE:
        {
            return true;
        }
        case WALK_FAST:
        {
            return true;
        }
        case DASHING:
        {
            return true;
        }
        case RUNNING:
        {
            return true;
        }
        case CROUCHING:
        {
            return true;
        }
        case LANDING:
        {
            return true;
        }
        case SHIELD:
        {
            return true;
        }
        case EDGE_TEETERING:
        {
            return true;
        }
        case EDGE_TEETERING_START:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}

bool TransitionHelper::canDash(ACTION action)
{
    switch(action)
    {
        case STANDING:
        {
            return true;
        }
        case DASHING:
        {
            return true;
        }
        case LANDING:
        {
            return true;
        }
        case EDGE_TEETERING:
        {
            return true;
        }
        case EDGE_TEETERING_START:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}

bool TransitionHelper::canSmash(ACTION action)
{
    switch(action)
    {
        case STANDING:
        {
            return true;
        }
        case WALK_SLOW:
        {
            return true;
        }
        case WALK_MIDDLE:
        {
            return true;
        }
        case WALK_FAST:
        {
            return true;
        }
        case KNEE_BEND:
        {
            return true;
        }
        case CROUCHING:
        {
            return true;
        }
        case LANDING:
        {
            return true;
        }
        case EDGE_TEETERING:
        {
            return true;
        }
        case EDGE_TEETERING_START:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}

bool TransitionHelper::canCrouch(ACTION action)
{
    switch(action)
    {
        case STANDING:
        {
            return true;
        }
        case WALK_SLOW:
        {
            return true;
        }
        case WALK_MIDDLE:
        {
            return true;
        }
        case WALK_FAST:
        {
            return true;
        }
        case DASHING:
        {
            return true;
        }
        case RUNNING:
        {
            return true;
        }
        case KNEE_BEND:
        {
            return true;
        }
        case CROUCHING:
        {
            return true;
        }
        case LANDING:
        {
            return true;
        }
        case EDGE_TEETERING:
        {
            return true;
        }
        case EDGE_TEETERING_START:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}
