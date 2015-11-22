#ifndef EDGESTALL_H
#define EDGESTALL_H

#include "Chain.h"

//Do a fully invincible edge stall
class EdgeStall : public Chain
{

public:

    FullJump(GameState *state);
    ~FullJump();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();
};

#endif
