#ifndef KILL_OPPONENT_H
#define KILL_OPPONENT_H

#include "Goal.h"
#include "../Gamestate.h"

class KillOpponent : public Goal
{
public:
    KillOpponent(GameState *state);
    ~KillOpponent();
    //Determine what the best strategy is, based on the current matchup / config
    //TODO: Again, we're just handling the Fox v Marth on FD matchup. So this will always be "bait" for now
    void Strategize();
};

#endif
