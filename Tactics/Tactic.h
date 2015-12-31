#ifndef TACTIC_H
#define TACTIC_H

#include <typeinfo>

#include "../Chains/Chain.h"
#include "../GameState.h"

//The tactic is a short term actionable objective
class Tactic
{

public:
    Tactic(){m_state = GameState::Instance();};
    virtual ~Tactic(){};
    //Determine what tactic to employ in order to further our strategy, based on game state
    virtual void DetermineChain() = 0;
    virtual bool IsInterruptible(){return m_chain->IsInterruptible();};

protected:

    //Returns if the given state allows us to perform any action
    bool ReadyForAction(uint a)
    {
        switch(a)
        {
            case STANDING:
                return true;
            case WALK_SLOW:
                return true;
            case WALK_MIDDLE:
                return true;
            case WALK_FAST:
                return true;
            case KNEE_BEND:
                return true;
            case CROUCHING:
                return true;
            case EDGE_TEETERING:
                return true;
            default:
                return false;
        }
        return false;
    }

    Chain *m_chain;
    GameState *m_state;
};

#define CreateChain(TYPE) if(m_chain==NULL){m_chain = new TYPE();} \
    if(typeid(*m_chain) != typeid(TYPE)){delete m_chain;m_chain = new TYPE();}
#define CreateChain2(TYPE, ARG) if(m_chain==NULL){m_chain = new TYPE(ARG);} \
    if(typeid(*m_chain) != typeid(TYPE)){delete m_chain;m_chain = new TYPE(ARG);}
#define CreateChain3(TYPE, ARG1, ARG2) if(m_chain==NULL){m_chain = new TYPE(ARG1, ARG2);} \
    if(typeid(*m_chain) != typeid(TYPE)){delete m_chain;m_chain = new TYPE(ARG1, ARG2);}

#endif
