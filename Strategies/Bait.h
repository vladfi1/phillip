#ifndef BAIT_H
#define BAIT_H

#include "Strategy.h"
//With this strategy, we're trying to bait our opponent into making a mistake, and then capitalizing on it.
class Bait : public Strategy
{

public:

    Bait(GameState *state);
    ~Bait();

    //Determine what tactic to employ in order to further our strategy
    void DetermineTactic();

};

#endif
