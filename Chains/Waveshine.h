#ifndef WAVESHINE_H
#define WAVESHINE_H

#include "Chain.h"

//Shine into wavedash
class Waveshine : public Chain
{

public:

    Waveshine();
    ~Waveshine();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    uint m_frameJumped;
    uint m_frameShined;
    uint m_hitlagFrames;
    uint m_frameKneeBend;
    uint m_airdodgeFrame;
    bool m_isBusy;
};

#endif
