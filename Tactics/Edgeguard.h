#ifndef EDGEGUARD_H
#define EDGEGUARD_H

#include "Tactic.h"

//With this strategy, we're trying to keep our opponent off the stage and make them die off the bottom
class Edgeguard : public Tactic
{

public:

    Edgeguard();
    ~Edgeguard();

    void DetermineChain();

};

#endif
