#ifndef SPOTDODGE_H
#define SPOTDODGE_H

#include "Chain.h"

//Do a spot dodge. aka down dodge
class SpotDodge : public Chain
{

public:

    SpotDodge();
    ~SpotDodge();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    bool m_isReverseFacing;
    bool m_hasShielded;
    bool m_hasSpotDodged;
};

#endif
