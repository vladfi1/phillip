#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>

#include <chrono>
#include <thread>

#include "GameState.h"
#include "MemoryWatcher.h"
#include "Controller.h"
#include "Serial.hpp"

using namespace std;

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
        const char *env_XDG_DATA_HOME = std::getenv("XDG_DATA_HOME");
        if(env_XDG_DATA_HOME == NULL)
        {
            //Try $HOME/.local/share next
            std::string backup_path = home_path + "/.local/share/dolphin-emu";
            if(stat(backup_path.c_str(), &buffer) != 0)
            {
                std::cout << "ERROR: $XDG_DATA_HOME was empty and so was $HOME/.dolphin-emu and $HOME/.local/share/dolphin-emu " \
                    "Are you sure Dolphin is installed? Make sure it is, and then run the CPU again." << std::endl;
                exit(-1);
            }
            else
            {
                mem_watcher_path = backup_path;
                mem_watcher_path += "/MemoryWatcher/";
                pipe_path = backup_path;
                pipe_path += "/Pipes/";
            }
        }
        else
        {
            mem_watcher_path = env_XDG_DATA_HOME;
            mem_watcher_path += "/MemoryWatcher/";
            pipe_path = env_XDG_DATA_HOME;
            pipe_path += "/Pipes/";
        }
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

void PrintState(GameMemory& memory)
{
    std::cout << "p1 percent: " << memory.player_one.percent << std::endl;
    std::cout << "p2 percent: " << memory.player_two.percent << std::endl;
    std::cout << "p1 stock: " << memory.player_one.stock << std::endl;
    std::cout << "p2 stock: " << memory.player_two.stock << std::endl;
    std::cout << "p1 character: " << memory.player_one.character << std::endl;
    std::cout << "p2 character: " << memory.player_two.character << std::endl;
    if(memory.player_one.facing)
    {
        std::cout << "p1 facing: right" << std::endl;
    }
    else
    {
        std::cout << "p1 facing: left" << std::endl;

    }
    if(memory.player_two.facing)
    {
        std::cout << "p2 facing: right" << std::endl;
    }
    else
    {
        std::cout << "p2 facing: left" << std::endl;
    }
    std::cout << "stage: " << std::hex << memory.stage << std::endl;
    std::cout << "frame: " << std::dec << memory.frame << std::endl;
    std::cout << "menu state: " << memory.menu_state << std::endl;
    std::cout << "p2 pointer x: " << memory.player_two_pointer_x << std::endl;
    std::cout << "p2 pointer y: " << memory.player_two_pointer_y << std::endl;

    std::cout << "p1 x: " << std::fixed << std::setprecision(10) << memory.player_one.x << std::endl;
    std::cout << "p1 y: " << std::fixed << std::setprecision(10) << memory.player_one.y << std::endl;

    std::cout << "p2 x: " << std::fixed << std::setprecision(10) << memory.player_two.x << std::endl;
    std::cout << "p2 y: " << std::fixed << std::setprecision(10) << memory.player_two.y << std::endl;

    std::cout << "p1 action: " << std::hex << memory.player_one.action << std::endl;
    std::cout << "p2 action: " << std::hex << memory.player_two.action << std::endl;

    std::cout << "p1 action count: " << std::dec << memory.player_one.action_counter << std::endl;
    std::cout << "p2 action count: " << std::dec << memory.player_two.action_counter << std::endl;

    std::cout << "p1 action frame: " << std::dec << memory.player_one.action_frame << std::endl;
    std::cout << "p2 action frame: " << std::dec << memory.player_two.action_frame << std::endl;

    if(memory.player_one.invulnerable)
    {
        std::cout << "p1 invulnerable" << std::endl;
    }
    else
    {
        std::cout << "p1 not invulnerable" << std::endl;
    }
    if(memory.player_two.invulnerable)
    {
        std::cout << "p2 invulnerable" << std::endl;
    }
    else
    {
        std::cout << "p2 not invulnerable" << std::endl;
    }

    if(memory.player_one.charging_smash)
    {
        std::cout << "p1 charging a smash" << std::endl;
    }
    else
    {
        std::cout << "p1 not charging a smash" << std::endl;
    }

    if(memory.player_two.charging_smash)
    {
        std::cout << "p2 charging a smash" << std::endl;
    }
    else
    {
        std::cout << "p2 not charging a smash" << std::endl;
    }

    std::cout << "p1 hitlag frames left: " << memory.player_one.hitlag_frames_left << std::endl;
    std::cout << "p2 hitlag frames left: " << memory.player_two.hitlag_frames_left << std::endl;

    std::cout << "p1 hitstun frames left: " << memory.player_one.hitstun_frames_left << std::endl;
    std::cout << "p2 hitstun frames left: " << memory.player_two.hitstun_frames_left << std::endl;

    std::cout << "p1 jumps left: " << memory.player_one.jumps_left << std::endl;
    std::cout << "p2 jumps left: " << memory.player_two.jumps_left << std::endl;

    if(memory.player_one.on_ground)
    {
        std::cout << "p1 on ground" << std::endl;
    }
    else
    {
        std::cout << "p1 in air" << std::endl;
    }
    if(memory.player_two.on_ground)
    {
        std::cout << "p2 on ground" << std::endl;
    }
    else
    {
        std::cout << "p2 in air" << std::endl;
    }

    std::cout << "p1 speed x air self: " << memory.player_one.speed_air_x_self << std::endl;
    std::cout << "p2 speed x air self: " << memory.player_two.speed_air_x_self << std::endl;

    std::cout << "p1 speed y self: " << memory.player_one.speed_y_self << std::endl;
    std::cout << "p2 speed y self: " << memory.player_two.speed_y_self << std::endl;

    std::cout << "p1 speed x attack: " << memory.player_one.speed_x_attack << std::endl;
    std::cout << "p2 speed x attack: " << memory.player_two.speed_x_attack << std::endl;

    std::cout << "p1 speed y attack: " << memory.player_one.speed_y_attack << std::endl;
    std::cout << "p2 speed y attack: " << memory.player_two.speed_y_attack << std::endl;

    std::cout << "p1 speed x ground self: " << memory.player_one.speed_ground_x_self << std::endl;
    std::cout << "p2 speed x ground self: " << memory.player_two.speed_ground_x_self << std::endl;
}

int main()
{
    //Do some first-time setup
    FirstTimeSetup();

    //GameState *state = GameState::Instance();
    Controller controller("cpu1");

    MemoryWatcher watcher;
    GameMemory memory;
    ControllerState controllerState;
    
    uint last_frame = 0;
    uint record_count = 0;
    
    const uint recordFrames = 60 * 60;
    
    WriteBuffer writeBuffer;
    
    for(; record_count < 1; ++record_count)
    {
        string recordFile = "testRecord" + std::to_string(record_count);
        
        ofstream fout;
        fout.open(recordFile, ios::binary | ios::out);

        for(uint frame = 0; frame < recordFrames;)
        {
            //controller->pressButton(Controller::BUTTON_D_RIGHT);
            while(!watcher.ReadMemory(memory)) {}
            //controller->releaseButton(Controller::BUTTON_D_RIGHT);
            
            if (memory.frame > last_frame + 1)
            {
                std::cout << "Missed frames " << last_frame + 1 << "-" << memory.frame - 1 << std::endl;
            }
            
            last_frame = memory.frame;
            
            if (memory.menu_state == IN_GAME)
            {
                controller.sendState(controllerState);
                fout.write(reinterpret_cast<char*>(&memory), sizeof(GameMemory));
                fout.write(reinterpret_cast<char*>(&controllerState), sizeof(ControllerState));
                ++frame;
            }
        }
        
        //fout.write(writeBuffer.getBuf(), writeBuffer.getSize());
        fout.close();
    }
    
    return EXIT_SUCCESS;
}
