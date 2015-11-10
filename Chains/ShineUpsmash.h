#ifndef SHINEUPSMASH_H
#define SHINEUPSMASH_H

#include "Chain.h"

//Jump cancel shine into upsmash
class ShineUpsmash : public Chain
{

public:

    ShineUpsmash(GameState *state);
    ~ShineUpsmash();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();
};

#endif
