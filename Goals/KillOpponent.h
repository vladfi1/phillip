#ifndef KILL_OPPONENT_H
#define KILL_OPPONENT_H

#include "Goal.h"
#include "../Gamestate.h"

class KillOpponent : public Goal
{
public:
    KillOpponent(GameState *state);
    ~KillOpponent();
    //Determine what the best strategy is
    void Strategize();
};

#endif
