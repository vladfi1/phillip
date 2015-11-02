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

#include "Controller.h"

Controller *controller;

struct GameState
{
	uint player_one_percent;
	uint player_one_stock;
	//True is right, false is left
	bool player_one_facing;
	float player_one_x;
	float player_one_y;
	uint player_one_action;

	uint player_two_percent;
	uint player_two_stock;
	//True is right, false is left
	bool player_two_facing;
	float player_two_x;
	float player_two_y;
	uint player_two_action;

	uint frame;
};

//Returns whether we're done with the combo or not
// end_in_shine - End inside the shine, so we can jump out of it for another combo
bool Multishine(uint frame, bool end_in_shine)
{
    switch(frame % 15)
    {   case 0:
        {
            return true;
        }
        case 1:
        {
            //Down-B
			controller->pressButton(Controller::BUTTON_B);
			controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
            if(end_in_shine)
            {
                return true;
            }
            break;
        }
        case 4:
        {
            //Let go of Down-B
			controller->releaseButton(Controller::BUTTON_B);
			controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);

            //Jump
			controller->pressButton(Controller::BUTTON_Y);

            break;
        }
        case 5:
        {
			controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
        case 7:
        {
            //Down-B again
			controller->pressButton(Controller::BUTTON_B);
			controller->tiltAnalog(Controller::BUTTON_MAIN, 0, .5);
            break;
        }
        case 8:
        {
            //Let go of Down-B
			controller->releaseButton(Controller::BUTTON_B);
			controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
            break;
        }
    }
    return false;
}

bool SHDL(uint frame)
{
    switch(frame % 27)
    {   case 0:
        {
            return true;
        }
        case 1:
        {
            //Jump
			controller->pressButton(Controller::BUTTON_Y);
            break;
        }
        case 2:
        {
            //let go of jump
			controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
        case 4:
        {
            //Laser
			controller->pressButton(Controller::BUTTON_B);
            break;
        }
        case 5:
        {
            //let go of Laser
			controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
        case 7:
        {
            //Laser
			controller->pressButton(Controller::BUTTON_B);
            break;
        }
        case 18:
        {
            //let go of Laser
			controller->releaseButton(Controller::BUTTON_Y);
            break;
        }
    }

    return false;
}

int main()
{
    int shmid;
    key_t key;
    char *shm;
    GameState *state;
	controller = new Controller();

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
    int shinecount = 0;
    int lasercount = 0;
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

			Multishine(state->frame, false);
			continue;

            //double-shine 9 times
            if(shinecount < 9)
            {
                if(Multishine(state->frame, false) == true)
                {
                    shinecount++;
                }
                continue;
            }

            //End inside a shine
            if(shinecount < 10)
            {
                if(Multishine(state->frame, true) == true)
                {
                    shinecount++;
                }
                continue;
            }

            //Let go of shine shine
            if(shinecount < 11)
            {
                //Let go of Down-B
				controller->releaseButton(Controller::BUTTON_B);
				controller->tiltAnalog(Controller::BUTTON_MAIN, .5, .5);
                shinecount++;
                continue;
            }

            //Should be ready to jump now

            //SHDL 3 times
            if(lasercount < 3)
            {
                if(SHDL(state->frame) == true)
                {
                    lasercount ++;
                }
                continue;
            }
            shinecount = 0;
            lasercount = 0;
        }
    }

	return EXIT_SUCCESS;
}
