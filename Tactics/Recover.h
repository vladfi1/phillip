#ifndef RECOVER_H
#define RECOVER_H

#include "Tactic.h"

//Keep the opponent in the air
class Recover : public Tactic
{

public:
    Recover();
    ~Recover();
    void DetermineChain();

};

#endif
