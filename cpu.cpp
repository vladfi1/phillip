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
	Goal *goal = new KillOpponent(state);

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

            goal->Strategize();
        }
    }

	return EXIT_SUCCESS;
}
