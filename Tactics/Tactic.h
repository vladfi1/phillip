#ifndef TACTIC_H
#define TACTIC_H

#include <typeinfo>

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

#define CreateChain(TYPE) if(m_chain==NULL){m_chain = new TYPE(m_state);} \
    if(typeid(*m_chain) != typeid(TYPE)){delete m_chain;m_chain = new TYPE(m_state);}
#define CreateChain2(TYPE, BUTTON) if(m_chain==NULL){m_chain = new TYPE(m_state, BUTTON);} \
    if(typeid(*m_chain) != typeid(TYPE)){delete m_chain;m_chain = new TYPE(m_state, BUTTON);}

#endif
