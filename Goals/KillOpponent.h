#ifndef KILL_OPPONENT_H
#define KILL_OPPONENT_H

#include "Goal.h"
#include "../GameState.h"

class KillOpponent : public Goal
{
public:
    KillOpponent();
    ~KillOpponent();
    //Determine what the best strategy is
    void Strategize();
};

#endif
