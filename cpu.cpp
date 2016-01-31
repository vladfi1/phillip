#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>

#include "Goals/KillOpponent.h"
#include "Goals/NavigateMenu.h"

#include "GameState.h"
#include "MemoryWatcher.h"

void FirstTimeSetup()
{
    struct passwd *pw = getpwuid(getuid());
    std::string home_path = std::string(pw->pw_dir);
    std::string legacy_config_path = home_path + "/.dolphin-emu";
    std::string mem_watcher_path;
    std::string pipe_path;

    struct stat buffer;
    if(stat(legacy_config_path.c_str(), &buffer) != 0)
    {
        //If the legacy app path is not present, see if the new one is
        const char* env_XDG_DATA_HOME = std::getenv("XDG_DATA_HOME");
        if(env_XDG_DATA_HOME == NULL)
        {
            std::cout << "ERROR: $XDG_DATA_HOME was empty and so was $HOME/.dolphin-emu." \
                "Make sure to install Dolphin first and try again." << std::endl;
            exit(-1);
        }
        mem_watcher_path = env_XDG_DATA_HOME;
        mem_watcher_path += "/MemoryWatcher/";
        pipe_path = env_XDG_DATA_HOME;
        pipe_path += "/Pipes/";
    }
    else
    {
        mem_watcher_path = legacy_config_path + "/MemoryWatcher/";
        pipe_path = legacy_config_path + "/Pipes/";
    }

    //Create the MemoryWatcher directory if it doesn't already exist
    if(stat(mem_watcher_path.c_str(), &buffer) != 0)
    {
        if(mkdir(mem_watcher_path.c_str(), 0775) != 0)
        {
            std::cout << "ERROR: Could not create the directory: \"" << mem_watcher_path << "\". Dolphin seems to be installed, " \
                "But this is not working for some reason. Maybe permissions?" << std::endl;
            exit(-1);
        }
        std::cout << "WARNING: Had to create a MemoryWatcher directory in Dolphin just now. " \
            "You may need to restart Dolphin and the CPU in order for this to work. (You should only see this warning once)" << std::endl;
    }

    std::ifstream src("Locations.txt", std::ios::in);
    std::ofstream dst(mem_watcher_path + "/Locations.txt", std::ios::out);
    dst << src.rdbuf();

    //Create the Pipes directory if it doesn't already exist
    if(stat(pipe_path.c_str(), &buffer) != 0)
    {
        if(mkdir(pipe_path.c_str(), 0775) != 0)
        {
            std::cout << "ERROR: Could not create the directory: \"" << pipe_path << "\". Dolphin seems to be installed, " \
                "But this is not working for some reason. Maybe permissions?" << std::endl;
            exit(-1);
        }
        std::cout << "WARNING: Had to create a Pipes directory in Dolphin just now. " \
            "You may need to restart Dolphin and the CPU in order for this to work. (You should only see this warning once)" << std::endl;
    }
}

void PrintState(GameState* state)
{
    std::cout << "p1 percent: " << state->m_memory->player_one_percent << std::endl;
    std::cout << "p2 percent: " << state->m_memory->player_two_percent << std::endl;
    std::cout << "p1 stock: " << state->m_memory->player_one_stock << std::endl;
    std::cout << "p2 stock: " << state->m_memory->player_two_stock << std::endl;
    std::cout << "p1 character: " << state->m_memory->player_one_character << std::endl;
    std::cout << "p2 character: " << state->m_memory->player_two_character << std::endl;
    if(state->m_memory->player_one_facing)
    {
        std::cout << "p1 facing: right" << std::endl;
    }
    else
    {
        std::cout << "p1 facing: left" << std::endl;

    }
    if(state->m_memory->player_two_facing)
    {
        std::cout << "p2 facing: right" << std::endl;
    }
    else
    {
        std::cout << "p2 facing: left" << std::endl;
    }
    std::cout << "stage: " << std::hex << state->m_memory->stage << std::endl;
    std::cout << "frame: " << std::dec << state->m_memory->frame << std::endl;
    std::cout << "menu state: " << state->m_memory->menu_state << std::endl;
    std::cout << "p2 pointer x: " << state->m_memory->player_two_pointer_x << std::endl;
    std::cout << "p2 pointer y: " << state->m_memory->player_two_pointer_y << std::endl;

    std::cout << "p1 x: " << std::fixed << std::setprecision(10) << state->m_memory->player_one_x << std::endl;
    std::cout << "p1 y: " << std::fixed << std::setprecision(10) << state->m_memory->player_one_y << std::endl;

    std::cout << "p2 x: " << std::fixed << std::setprecision(10) << state->m_memory->player_two_x << std::endl;
    std::cout << "p2 y: " << std::fixed << std::setprecision(10) << state->m_memory->player_two_y << std::endl;

    std::cout << "p1 action: " << std::hex << state->m_memory->player_one_action << std::endl;
    std::cout << "p2 action: " << std::hex << state->m_memory->player_two_action << std::endl;

    std::cout << "p1 action count: " << std::dec << state->m_memory->player_one_action_counter << std::endl;
    std::cout << "p2 action count: " << std::dec << state->m_memory->player_two_action_counter << std::endl;

    std::cout << "p1 action frame: " << std::dec << state->m_memory->player_one_action_frame << std::endl;
    std::cout << "p2 action frame: " << std::dec << state->m_memory->player_two_action_frame << std::endl;

    if(state->m_memory->player_one_invulnerable)
    {
        std::cout << "p1 invulnerable" << std::endl;
    }
    else
    {
        std::cout << "p1 not invulnerable" << std::endl;
    }
    if(state->m_memory->player_two_invulnerable)
    {
        std::cout << "p2 invulnerable" << std::endl;
    }
    else
    {
        std::cout << "p2 not invulnerable" << std::endl;
    }

    if(state->m_memory->player_one_charging_smash)
    {
        std::cout << "p1 charging a smash" << std::endl;
    }
    else
    {
        std::cout << "p1 not charging a smash" << std::endl;
    }

    if(state->m_memory->player_two_charging_smash)
    {
        std::cout << "p2 charging a smash" << std::endl;
    }
    else
    {
        std::cout << "p2 not charging a smash" << std::endl;
    }

    std::cout << "p1 hitlag frames left: " << state->m_memory->player_one_hitlag_frames_left << std::endl;
    std::cout << "p2 hitlag frames left: " << state->m_memory->player_two_hitlag_frames_left << std::endl;

    std::cout << "p1 hitstun frames left: " << state->m_memory->player_one_hitstun_frames_left << std::endl;
    std::cout << "p2 hitstun frames left: " << state->m_memory->player_two_hitstun_frames_left << std::endl;

    std::cout << "p1 jumps left: " << state->m_memory->player_one_jumps_left << std::endl;
    std::cout << "p2 jumps left: " << state->m_memory->player_two_jumps_left << std::endl;

    if(state->m_memory->player_one_on_ground)
    {
        std::cout << "p1 on ground" << std::endl;
    }
    else
    {
        std::cout << "p1 in air" << std::endl;
    }
    if(state->m_memory->player_two_on_ground)
    {
        std::cout << "p2 on ground" << std::endl;
    }
    else
    {
        std::cout << "p2 in air" << std::endl;
    }

    std::cout << "p1 speed x air self: " << state->m_memory->player_one_speed_air_x_self << std::endl;
    std::cout << "p2 speed x air self: " << state->m_memory->player_two_speed_air_x_self << std::endl;

    std::cout << "p1 speed y self: " << state->m_memory->player_one_speed_y_self << std::endl;
    std::cout << "p2 speed y self: " << state->m_memory->player_two_speed_y_self << std::endl;

    std::cout << "p1 speed x attack: " << state->m_memory->player_one_speed_x_attack << std::endl;
    std::cout << "p2 speed x attack: " << state->m_memory->player_two_speed_x_attack << std::endl;

    std::cout << "p1 speed y attack: " << state->m_memory->player_one_speed_y_attack << std::endl;
    std::cout << "p2 speed y attack: " << state->m_memory->player_two_speed_y_attack << std::endl;

    std::cout << "p1 speed x ground self: " << state->m_memory->player_one_speed_ground_x_self << std::endl;
    std::cout << "p2 speed x ground self: " << state->m_memory->player_two_speed_ground_x_self << std::endl;
}

int main()
{
    //Do some first-time setup
    FirstTimeSetup();

    GameState *state = GameState::Instance();

    MemoryWatcher *watcher = new MemoryWatcher();
    uint last_frame = 0;
    //Get our goal
    Goal *goal = NULL;
    MENU current_menu;

    //Main frame loop
    for(;;)
    {
        //If we get a new frame, process it. Otherwise, keep reading memory
        if(!watcher->ReadMemory())
        {
            continue;
        }

        //PrintState(state);

        current_menu = (MENU)state->m_memory->menu_state;

        //Spinloop until we get a new frame
        if(state->m_memory->frame != last_frame)
        {
            if(state->m_memory->frame > last_frame+1)
            {
                std::cout << "WARNING: FRAME MISSED" << std::endl;
            }
            last_frame = state->m_memory->frame;

            //If we're in a match, play the match!
            if(state->m_memory->menu_state == IN_GAME)
            {
                if(goal == NULL )
                {
                    goal = new KillOpponent();
                }
                if(typeid(*goal) != typeid(KillOpponent))
                {
                    delete goal;
                    goal = new KillOpponent();
                }
                goal->Strategize();
            }
            //If we're in a menu, then let's navigate the menu
            else if(state->m_memory->menu_state == CHARACTER_SELECT ||
                state->m_memory->menu_state == STAGE_SELECT ||
                state->m_memory->menu_state == POSTGAME_SCORES)
            {
                if(goal == NULL )
                {
                    goal = new NavigateMenu();
                }
                if(typeid(*goal) != typeid(NavigateMenu))
                {
                    delete goal;
                    goal = new NavigateMenu();
                }
                goal->Strategize();
            }
        }
        //If the menu changed
        else if(current_menu != state->m_memory->menu_state)
        {
            last_frame = 1;
            current_menu = (MENU)state->m_memory->menu_state;
        }
    }

    return EXIT_SUCCESS;
}
