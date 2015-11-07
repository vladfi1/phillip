#ifndef CLOSE_DISTANCE_H
#define CLOSE_DISTANCE_H

#include "Tactic.h"

//This tactic can be used to safely get in close with our opponent if they are not near
class CloseDistance : public Tactic
{

public:

    CloseDistance(GameState *state);
    ~CloseDistance();
    void DetermineChain();

};

#endif
