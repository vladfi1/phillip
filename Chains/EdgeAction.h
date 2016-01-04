#ifndef EDGEACTION_H
#define EDGEACTION_H

#include "Chain.h"
#include "../Controller.h"

//Perform an action to get up from the edge
class EdgeAction : public Chain
{

public:

    EdgeAction(Controller::BUTTON b, uint waitFrames = 0);
    ~EdgeAction();

    void PressButtons();
    bool IsInterruptible();

private:
    Controller::BUTTON m_button;
    bool m_readyToInterrupt;
    uint m_waitFrames;
};

#endif
