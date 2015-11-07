#ifndef STRATEGY_H
#define STRATEGY_H

#include "../Tactics/Tactic.h"
#include "../Gamestate.h"

//The strategy is a high level way of accomplishing the top level goal. You might call it a "playstyle"
//  or "gameplan".
class Strategy
{

public:
    Strategy(GameState *state){m_state = state;};
    virtual ~Strategy(){};
    //Determine what tactic to employ in order to further our strategy
    // This decision is made on the basis of the game state
    virtual void DetermineTactic() = 0;

protected:
    Tactic *m_tactic;
    GameState *m_state;
};

#endif
