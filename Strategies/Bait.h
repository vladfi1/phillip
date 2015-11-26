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

    //Is the given action an attack?
    bool isAttacking(ACTION a);

private:
    //Frame that the player's attack started
    //0 means no attack
    uint m_attackFrame;
    //The action the opponent was in last frame
    ACTION m_lastAction;
    //Did the enemy's action change from last frame?
    bool m_actionChanged;
    bool m_shieldedAttack;

};

#endif
