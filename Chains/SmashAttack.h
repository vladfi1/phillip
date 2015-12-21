#ifndef SMASHATTACK_H
#define SMASHATTACK_H

#include "Chain.h"
#include "../Controller.h"

//Perform a specified smash attack
class SmashAttack : public Chain
{

public:

    enum DIRECTION
    {
        UP, DOWN, LEFT, RIGHT,
    };

    SmashAttack(DIRECTION d, uint charge_frames);
    ~SmashAttack();

    void PressButtons();
    bool IsInterruptible();

private:
    DIRECTION m_direction;
    uint m_charge_frames;
};

#endif
