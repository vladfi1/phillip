#ifndef POWERSHIELD_H
#define POWERSHIELD_H

#include "Chain.h"

//Powershield an incoming attack
class Powershield : public Chain
{

public:

    Powershield(GameState *state, uint startFrame);
    ~Powershield();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    uint m_frame_shielded;
    uint m_startFrame;
    bool m_isReverseFacing;
};

#endif
