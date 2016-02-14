#ifndef WAVEDASH_H
#define WAVEDASH_H

#include "Chain.h"

//Wavedash
class Wavedash : public Chain
{

public:

    //True arg means wavedash to the right
    Wavedash(bool isRight);
    ~Wavedash();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    uint m_frameJumped;
    uint m_hitlagFrames;
    uint m_frameKneeBend;
    bool m_isright;
};

#endif
