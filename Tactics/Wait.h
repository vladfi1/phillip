#ifndef WAIT_H
#define WAIT_H

#include "Tactic.h"

//This tactic can be used to safely get in close with our opponent if they are not near
class Wait : public Tactic
{

public:

    Wait();
    ~Wait();
    void DetermineChain();

};

#endif
