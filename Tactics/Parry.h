#ifndef PARRY_H
#define PARRY_H

#include "Tactic.h"

//Dodge an attack. This could mean powershielding, jumping out of the way, spot dodging, whatever.
class Parry : public Tactic
{

public:

    //Second param is the frame the attack we're parrying started
    Parry(GameState *state, uint frame);
    ~Parry();
    void DetermineChain();

private:
    uint m_startFrame;
};

#endif
