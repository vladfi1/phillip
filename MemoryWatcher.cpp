#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <pwd.h>
#include <string>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <cstdlib>
#include <sys/stat.h>

#include "MemoryWatcher.h"

// TODO: pass in watcher location
MemoryWatcher::MemoryWatcher()
{
    struct passwd *pw = getpwuid(getuid());
    std::string home_path = std::string(pw->pw_dir);
    std::string legacy_config_path = home_path + "/.dolphin-emu";
    std::string mem_watcher_path;

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
            mem_watcher_path = backup_path;
            mem_watcher_path += "/MemoryWatcher/";
        }
        else
        {
            mem_watcher_path = env_XDG_DATA_HOME;
            mem_watcher_path += "/MemoryWatcher/";
        }
    }
    else
    {
        mem_watcher_path = legacy_config_path + "/MemoryWatcher/";
    }

    mem_watcher_path += "MemoryWatcher";

    m_file = socket(AF_UNIX, SOCK_DGRAM, 0);
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    unlink(mem_watcher_path.c_str());
    strncpy(addr.sun_path, mem_watcher_path.c_str(), sizeof(addr.sun_path) - 1);
    bind(m_file, (struct sockaddr*) &addr, sizeof(addr));
}

inline float asFloat(uint value_int)
{
    return reinterpret_cast<float&>(value_int);
}

bool MemoryWatcher::ReadMemory(GameMemory& memory)
{
    char buf[128];
    memset(buf, '\0', 128);

    struct sockaddr remaddr;
    socklen_t addr_len;
    recvfrom(m_file, buf, sizeof(buf), 0, &remaddr, &addr_len);
    std::stringstream ss(buf);
    std::string region, value;

    std::getline(ss, region, '\n');
    std::getline(ss, value, '\n');
    uint value_int;

    //Is this a followed pointer?
    std::size_t found = region.find(" ");
    if(found != std::string::npos)
    {
        std::string ptr = region.substr(found+1);
        std::string base = region.substr(0, found);
        uint ptr_int = std::stoul(ptr.c_str(), nullptr, 16);
        uint base_int = std::stoul(base.c_str(), nullptr, 16);

        //Player one
        if(base_int == 0x453130)
        {
            switch(ptr_int)
            {
                //Action
                case 0x70:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.action = value_int;
                    break;
                }
                //Action counter
                case 0x20CC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.action_counter = value_int;
                    break;
                }
                //Action frame
                case 0x8F4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.action_frame = asFloat(value_int);
                    break;
                }
                //Invulnerable
                case 0x19EC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        memory.player_one.invulnerable = false;
                    }
                    else
                    {
                        memory.player_one.invulnerable = true;
                    }
                    break;
                }
                //Hitlag
                case 0x19BC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.hitlag_frames_left = asFloat(value_int);
                    break;
                }
                //Hitstun
                case 0x23a0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.hitstun_frames_left = asFloat(value_int);
                    break;
                }
                //Is charging a smash?
                case 0x2174:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.action = value_int;
                    if(value_int == 2)
                    {
                        memory.player_one.charging_smash = true;
                    }
                    else
                    {
                        memory.player_one.charging_smash = false;
                    }
                    break;
                }
                //Jumps remaining
                case 0x19C8:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    value_int = value_int >> 24;
                    //TODO: This won't work for characters with multiple jumps
                    if(value_int > 1)
                    {
                        value_int = 0;
                    }
                    memory.player_one.jumps_left = value_int;
                    break;
                }
                //Is on ground?
                case 0x140:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        memory.player_one.on_ground = true;
                    }
                    else
                    {
                        memory.player_one.on_ground = false;
                    }
                    break;
                }
                //X air speed self
                case 0xE0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.speed_air_x_self = asFloat(value_int);
                    break;
                }
                //Y air speed self
                case 0xE4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.speed_y_self = asFloat(value_int);
                    break;
                }
                //X attack
                case 0xEC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.speed_x_attack = asFloat(value_int);
                    break;
                }
                //Y attack
                case 0xF0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.speed_y_attack = asFloat(value_int);
                    break;
                }
                //x ground self
                case 0x14C:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_one.speed_ground_x_self = asFloat(value_int);
                    break;
                }
                default:
                {
                    std::cout << "WARNING: Got an unexpected memory pointer: " << ptr_int << std::endl;
                }
            }
        }
        //Player two
        else if(base_int == 0x453FC0)
        {
            switch(ptr_int)
            {
                //Action
                case 0x70:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.action = value_int;
                    break;
                }
                //Action counter
                case 0x20CC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.action_counter = value_int;
                    break;
                }
                //Action frame
                case 0x8F4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.action_frame = asFloat(value_int);
                    break;
                }
                //Invulnerable
                case 0x19EC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        memory.player_two.invulnerable = false;
                    }
                    else
                    {
                        memory.player_two.invulnerable = true;
                    }
                    break;
                }
                //Hitlag
                case 0x19BC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.hitlag_frames_left = asFloat(value_int);
                    break;
                }
                //Hitstun
                case 0x23a0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.hitstun_frames_left = asFloat(value_int);
                    break;
                }
                //Is charging a smash?
                case 0x2174:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.action = value_int;
                    if(value_int == 2)
                    {
                        memory.player_two.charging_smash = true;
                    }
                    else
                    {
                        memory.player_two.charging_smash = false;
                    }
                    break;
                }
                //Jumps remaining
                case 0x19C8:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    value_int = value_int >> 24;
                    //TODO: This won't work for characters with multiple jumps
                    if(value_int > 1)
                    {
                        value_int = 0;
                    }
                    memory.player_two.jumps_left = value_int;
                    break;
                }
                //Is on ground?
                case 0x140:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        memory.player_two.on_ground = true;
                    }
                    else
                    {
                        memory.player_two.on_ground = false;
                    }
                    break;
                }
                //X air speed self
                case 0xE0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.speed_air_x_self = asFloat(value_int);
                    break;
                }
                //Y air speed self
                case 0xE4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.speed_y_self = asFloat(value_int);
                    break;
                }
                //X attack
                case 0xEC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.speed_x_attack = asFloat(value_int);
                    break;
                }
                //Y attack
                case 0xF0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.speed_y_attack = asFloat(value_int);
                    break;
                }
                //x ground self
                case 0x14C:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    memory.player_two.speed_ground_x_self = asFloat(value_int);
                    break;
                }
                default:
                {
                    std::cout << "WARNING: Got an unexpected memory pointer: " << ptr_int << std::endl;
                }
            }
        }
        else
        {
            std::cout << "WARNING: Got an unexpected memory base pointer: " << base_int << std::endl;
        }
    }
    //If not, it's a direct pointer
    else
    {
        uint region_int = std::stoul(region.c_str(), nullptr, 16);
        switch(region_int)
        {
            //Frame
            case 0x479D60:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.frame = value_int;
                break;
            }
            //Player 1 percent
            case 0x4530E0:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 16;
                memory.player_one.percent = value_int;
                break;
            }
            //Player 2 percent
            case 0x453F70:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 16;
                memory.player_two.percent = value_int;
                break;
            }
            //Player 1 stock
            case 0x45310E:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                memory.player_one.stock = value_int;

                break;
            }
            //Player 2 stock
            case 0x453F9E:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                memory.player_two.stock = value_int;
                break;
            }
            //Player 1 facing
            case 0x4530C0:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                bool facing = value_int >> 31;
                memory.player_one.facing = !facing;
                break;
            }
            //Player 2 facing
            case 0x453F50:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                bool facing = value_int >> 31;
                memory.player_two.facing = !facing;
                break;
            }
            //Player 1 x
            case 0x453090:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.player_one.x = asFloat(value_int);
                break;
            }
            //Player 2 x
            case 0x453F20:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.player_two.x = asFloat(value_int);
                break;
            }
            //Player 1 y
            case 0x453094:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.player_one.y = asFloat(value_int);
                break;
            }
            //Player 2 y
            case 0x453F24:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.player_two.y = asFloat(value_int);
                break;
            }
            //Player one character
            case 0x3F0E0A:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                memory.player_one.character = value_int;
                break;
            }
            //Player two character
            case 0x3F0E2E:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                memory.player_two.character = value_int;
                break;
            }
            //Menu state
            case 0x479d30:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.menu_state = value_int;
                break;
            }
            //Stage
            case 0x4D6CAD:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 16;
                memory.stage = value_int;
                break;
            }
            //p2 cursor x
            case 0x0111826C:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.player_two_pointer_x = asFloat(value_int);
                break;
            }
            //p2 cursor y
            case 0x01118270:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                memory.player_two_pointer_y = asFloat(value_int);
                break;
            }
            case 0x003F0E08:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                std::cout << std::hex << "P1: " << value_int << std::endl;
                break;
            }
        }
    }

    if(region == "00479D60")
    {
        return true;
    }
    return false;
}
