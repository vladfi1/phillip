#ifndef SHDL_H
#define SHDL_H

#include "Chain.h"

//Short hop double laser, no horizontal movement
class SHDL : public Chain
{

public:

    SHDL(GameState *state);
    ~SHDL();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
};

#endif
