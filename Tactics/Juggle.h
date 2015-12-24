#ifndef JUGGLE_H
#define JUGGLE_H

#include "Tactic.h"

//Keep the opponent in the air
class Juggle : public Tactic
{

public:
    Juggle();
    ~Juggle();
    void DetermineChain();

private:
    double m_roll_position;
};

#endif
