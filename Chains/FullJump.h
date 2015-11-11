#ifndef FULLJUMP_H
#define FULLJUMP_H

#include "Chain.h"

//Do a full jump (ie: not short hop)
class FullJump : public Chain
{

public:

    FullJump(GameState *state);
    ~FullJump();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();
};

#endif
