#ifndef JAB_H
#define JAB_H

#include "Chain.h"

//Do a single jab
class Jab : public Chain
{

public:

    Jab();
    ~Jab();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();
};

#endif
