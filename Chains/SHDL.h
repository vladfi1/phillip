#ifndef SHDL_H
#define SHDL_H

#include "Chain.h"

//Short hop double laser, no horizontal movement
class SHDL : public Chain
{

public:

    SHDL();
    ~SHDL();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    uint m_landedFrame;
    uint m_jumpedFrame;
    ACTION m_action;
    bool m_holdingLaser;
};

#endif
