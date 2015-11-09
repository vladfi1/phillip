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

#define CreateChain(TYPE) if(m_chain==NULL){m_chain = new TYPE(m_state);}if(typeid(*m_chain) != typeid(TYPE)){delete m_chain;m_chain = new TYPE(m_state);}

#endif
