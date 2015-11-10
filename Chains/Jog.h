#ifndef JOG_H
#define JOG_H

#include "Chain.h"

//Walk quickly, but not dash
class Jog : public Chain
{

public:

    Jog(GameState *state, bool);
    ~Jog();
    //Determine what buttons to press in order to execute our tactic
    void PressButtons();
    bool IsInterruptible();

private:
    bool m_isRight;
};

#endif
