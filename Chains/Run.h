#ifndef RUN_H
#define RUN_H

#include "Chain.h"

//Run in a given direction
class Run : public Chain
{

public:

    Run(bool);
    ~Run();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    bool m_isRight;
    bool m_isWavedashing;
    uint m_wavedashFrameStart;
};

#endif
