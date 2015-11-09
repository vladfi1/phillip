#ifndef POWERSHIELD_H
#define POWERSHIELD_H

#include "Chain.h"

//Powershield an incoming attack
class Powershield : public Chain
{

public:

    Powershield(GameState *state);
    ~Powershield();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
};

#endif
