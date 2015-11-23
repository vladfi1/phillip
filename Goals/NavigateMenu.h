#ifndef NAVIGATE_MENU_H
#define NAVIGATE_MENU_H

#include "Goal.h"
#include "../Gamestate.h"

//We do all the menu logic here so as to not clutter up the lower goal objects space
class NavigateMenu : public Goal
{
public:
    NavigateMenu(GameState *state);
    ~NavigateMenu();

    void Strategize();

private:
    Controller *m_controller;
    bool m_emptiedInput;
};

#endif
