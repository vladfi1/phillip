#ifndef TACTIC_H
#define TACTIC_H

#include "../Chains/Chain.h"
#include "../Gamestate.h"

//The tactic is a short term actionable objective
class Tactic
{

public:
    Tactic(GameState *state){m_state = state;};
    virtual ~Tactic(){};
    //Determine what tactic to employ in order to further our strategy, based on game state
    virtual void DetermineChain() = 0;

protected:
    Chain *m_chain;
    GameState *m_state;
};

#endif
