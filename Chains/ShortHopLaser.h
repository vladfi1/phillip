#ifndef SHL_H
#define SHL_H

#include "Chain.h"

enum DIRECTION
{
    RETREATING,
    APPROACHING,
    UNMOVING,
};

//Short hop laser
class ShortHopLaser : public Chain
{

public:

    ShortHopLaser(DIRECTION direction);
    ~ShortHopLaser();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    DIRECTION m_direction;
    bool m_pressedBack;
};

#endif
