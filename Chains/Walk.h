#ifndef Walk_H
#define Walk_H

#include "Chain.h"

//Walk quickly, but not dash
class Walk : public Chain
{

public:

    Walk(bool);
    ~Walk();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    bool m_isRight;
};

#endif
