#ifndef MULTISHINE_H
#define MULTISHINE_H

#include "Chain.h"

//Multishines
class Multishine : public Chain
{

public:

    Multishine(GameState *state);
    ~Multishine();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();
};

#endif
