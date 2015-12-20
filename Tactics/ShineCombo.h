#ifndef SHINECOMBO_H
#define SHINECOMBO_H

#include "Tactic.h"

//Do a ground-based shine combo.
class ShineCombo : public Tactic
{

public:
    ShineCombo();
    ~ShineCombo();
    void DetermineChain();

};

#endif
