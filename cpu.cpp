#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <stdio.h>
#include <stdlib.h>
#include <iomanip>
#include <iostream>

#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>

#include "Goals/KillOpponent.h"
#include "Goals/NavigateMenu.h"

#include "Gamestate.h"

int main()
{
    int shmid;
    key_t key;
    char *shm;
    GameState *state;

	//return 0;
    key = 1337;

    /*
     * Locate the segment.
     */
    if ((shmid = shmget(key, sizeof(GameState), 0666)) < 0) {
        perror("shmget");
        exit(1);
    }

    /*
     * Now we attach the segment to our data space.
     */
    if ((shm = (char*)shmat(shmid, NULL, 0)) == (char *) -1) {
        perror("shmat");
        exit(1);
    }

    state = (GameState*)shm;

    std::cout << "p1 percent: " << state->player_one_percent << std::endl;
    std::cout << "p2 percent: " << state->player_two_percent << std::endl;
    std::cout << "p1 stock: " << state->player_one_stock << std::endl;
    std::cout << "p2 stock: " << state->player_two_stock << std::endl;
	if(state->player_one_facing)
	{
		std::cout << "p1 facing: right" << std::endl;

	}
	else
	{
		std::cout << "p1 facing: left" << std::endl;

	}
	if(state->player_two_facing)
	{
		std::cout << "p2 facing: right" << std::endl;

	}
	else
	{
		std::cout << "p2 facing: left" << std::endl;

	}
    std::cout << "frame: " << state->frame << std::endl;
	std::cout << "p1 x: " << std::fixed << std::setprecision(10) << state->player_one_x << std::endl;
	std::cout << "p1 y: " << std::fixed << std::setprecision(10) << state->player_one_y << std::endl;

	std::cout << "p2 x: " << std::fixed << std::setprecision(10) << state->player_two_x << std::endl;
	std::cout << "p2 y: " << std::fixed << std::setprecision(10) << state->player_two_y << std::endl;

	std::cout << "p1 action: " << std::hex << state->player_one_action << std::endl;
	std::cout << "p2 action: " << std::hex << state->player_two_action << std::endl;


    uint last_frame = state->frame;
    //Get our goal
	Goal *goal = NULL;
    MENU current_menu = (MENU)state->menu_state;

    //Main frame loop
    for(;;)
    {
        //Spinloop until we get a new frame
        if(state->frame > last_frame)
        {
            if(state->frame > last_frame+1)
            {
                std::cout << "WARNING: FRAME MISSED" << std::endl;
            }
            last_frame = state->frame;

            //If we're in a match, play the match!
            if(state->menu_state == IN_GAME)
            {
                if(goal == NULL )
                {
                    goal = new KillOpponent(state);
                }
                if(typeid(*goal) != typeid(KillOpponent))
                {
                    delete goal;
                    goal = new KillOpponent(state);
                }
                goal->Strategize();
            }
            //If we're in a menu, then let's navigate the menu
            else if(state->menu_state == CHARACTER_SELECT || state->menu_state == STAGE_SELECT)
            {
                if(goal == NULL )
                {
                    goal = new NavigateMenu(state);
                }
                if(typeid(*goal) != typeid(NavigateMenu))
                {
                    delete goal;
                    goal = new NavigateMenu(state);
                }
                goal->Strategize();
            }
        }
        //If the menu changed
        else if(current_menu != state->menu_state)
        {
            last_frame = 1;
            current_menu = (MENU)state->menu_state;
        }
    }

	return EXIT_SUCCESS;
}
