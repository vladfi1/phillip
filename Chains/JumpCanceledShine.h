#ifndef JUMPCANCELEDSHINE_H
#define JUMPCANCELEDSHINE_H

#include "Chain.h"

//Shine, and then short hop out of it. Interuptible during the jumping animation (grounded) for lead-ins
class JumpCanceledShine : public Chain
{

public:

    JumpCanceledShine(GameState *state);
    ~JumpCanceledShine();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();
};

#endif
