#ifndef MARTHKILLER_H
#define MARTHKILLER_H

#include "Chain.h"

//Roll backwards towards the stage, lightshield, hold diagonally down
class MarthKiller : public Chain
{

public:

    MarthKiller();
    ~MarthKiller();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    bool m_shielded;
    bool m_rolled;
    bool m_onRight;
    uint m_rollFrame;
    double m_shieldOffset;
};

#endif
