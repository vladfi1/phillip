#ifndef PARRY_H
#define PARRY_H

#include "Tactic.h"

//Dodge an attack. This could mean powershielding, jumping out of the way, spot dodging, whatever.
class Parry : public Tactic
{

public:

    Parry(GameState *state);
    ~Parry();
    void DetermineChain();

};

#endif
