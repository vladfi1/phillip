#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <stdio.h>
#include <stdlib.h>
#include <iomanip>
#include <iostream>

extern "C" {
#include <xdo.h>
}

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
bool Multishine(uint frame, xdo_t *xdo, bool end_in_shine)
{
    switch(frame % 15)
    {   case 0:
        {
            return true;
        }
        case 1:
        {
            //Down-B
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "2", 0);
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "k", 0);
            if(end_in_shine)
            {
                return true;
            }
            break;
        }
        case 4:
        {
            //Let go of Down-B
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "2", 0);
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "k", 0);

            //Jump
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "4", 0);

            break;
        }
        case 5:
        {
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "4", 0);
            break;
        }
        case 7:
        {
            //Down-B again
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "2", 0);
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "k", 0);
            break;
        }
        case 8:
        {
            //Let go of Down-B
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "2", 0);
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "k", 0);
            break;
        }
    }
    return false;
}

bool SHDL(uint frame, xdo_t *xdo)
{
    switch(frame % 27)
    {   case 0:
        {
            return true;
        }
        case 1:
        {
            //Jump
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "4", 0);
            break;
        }
        case 2:
        {
            //let go of jump
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "4", 0);
            break;
        }
        case 4:
        {
            //Laser
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "2", 0);
            break;
        }
        case 5:
        {
            //let go of Laser
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "2", 0);
            break;
        }
        case 7:
        {
            //Laser
            xdo_send_keysequence_window_down(xdo, CURRENTWINDOW, "2", 0);
            break;
        }
        case 18:
        {
            //let go of Laser
            xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "2", 0);
            break;
        }
    }

    return false;
}

main()
{
    int shmid;
    key_t key;
    char *shm, *s;
    GameState *state;

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

    /*
    1 = A
    2 = B
    3 = X
    4 = Y
    5 = Z

    WASD:
    ijkl
    */

    uint last_frame = state->frame;
	xdo_t *xdo = xdo_new(NULL);
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

			Multishine(state->frame, xdo, false);
			continue;

            //double-shine 9 times
            if(shinecount < 9)
            {
                if(Multishine(state->frame, xdo, false) == true)
                {
                    shinecount++;
                }
                continue;
            }

            //End inside a shine
            if(shinecount < 10)
            {
                if(Multishine(state->frame, xdo, true) == true)
                {
                    shinecount++;
                }
                continue;
            }

            //Let go of shine shine
            if(shinecount < 11)
            {
                //Let go of Down-B
                xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "2", 0);
                xdo_send_keysequence_window_up(xdo, CURRENTWINDOW, "k", 0);
                shinecount++;
                continue;
            }

            //Should be ready to jump now

            //SHDL 3 times
            if(lasercount < 3)
            {
                if(SHDL(state->frame, xdo) == true)
                {
                    lasercount ++;
                }
                continue;
            }
            shinecount = 0;
            lasercount = 0;
        }
    }
}
