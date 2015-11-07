#ifndef CHAIN_H
#define CHAIN_H

#include <sys/types.h>
#include "../Controller.h"
#include "../Gamestate.h"

//A chain is a series of button presses that creates a commonly reused set of actions. Examples include:
//  SHFFL'ing arials, SHDL, waveshine, etc...
class Chain
{

public:
    Chain(GameState *state){m_state = state;};
    virtual ~Chain(){};
    //Determine what buttons to press in order to execute our tactic
    virtual void PressButtons() = 0;

protected:

    Controller *m_controller;
    GameState *m_state;
    //What frame we started the chain on, so we know where we are in it going forward
    uint m_startingFrame;
    //The number of frames this chain will take from start to finish
    uint m_duration;
};

#endif
