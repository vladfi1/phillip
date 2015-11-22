#ifndef TRANSITION_H
#define TRANSITION_H

#include "../Gamestate.h"

//Helper functions for transitioning from one action state to another
class TransitionHelper
{

public:
    //Determine what tactic to employ in order to further our strategy
    static void Transition(ACTION from, ACTION to);

    //Can we perform one of these actions right now, with a given state?
    static bool canJump(ACTION a);
    static bool canDash(ACTION a);
    static bool canSmash(ACTION a);
    static bool canCrouch(ACTION a);
};

#endif
