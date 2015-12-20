#ifndef SPOTDODGE_H
#define SPOTDODGE_H

#include "Chain.h"

//Do a spot dodge. aka down dodge
class SpotDodge : public Chain
{

public:

    SpotDodge(uint startFrame);
    ~SpotDodge();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    uint m_startFrame;
    bool m_isReverseFacing;
};

#endif
