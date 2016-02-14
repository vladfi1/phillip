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

MemoryWatcher::MemoryWatcher()
{
    m_state = GameState::Instance();

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

bool MemoryWatcher::ReadMemory()
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
                    m_state->m_memory->player_one_action = value_int;
                    break;
                }
                //Action counter
                case 0x20CC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    m_state->m_memory->player_one_action_counter = value_int;
                    break;
                }
                //Action frame
                case 0x8F4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_action_frame = x;
                    break;
                }
                //Invulnerable
                case 0x19EC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        m_state->m_memory->player_one_invulnerable = false;
                    }
                    else
                    {
                        m_state->m_memory->player_one_invulnerable = true;
                    }
                    break;
                }
                //Hitlag
                case 0x19BC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_hitlag_frames_left = x;
                    break;
                }
                //Hitstun
                case 0x23a0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_hitstun_frames_left = x;
                    break;
                }
                //Is charging a smash?
                case 0x2174:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    m_state->m_memory->player_one_action = value_int;
                    if(value_int == 2)
                    {
                        m_state->m_memory->player_one_charging_smash = true;
                    }
                    else
                    {
                        m_state->m_memory->player_one_charging_smash = false;
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
                    m_state->m_memory->player_one_jumps_left = value_int;
                    break;
                }
                //Is on ground?
                case 0x140:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        m_state->m_memory->player_one_on_ground = true;
                    }
                    else
                    {
                        m_state->m_memory->player_one_on_ground = false;
                    }
                    break;
                }
                //X air speed self
                case 0xE0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_speed_air_x_self = x;
                    break;
                }
                //Y air speed self
                case 0xE4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_speed_y_self = x;
                    break;
                }
                //X attack
                case 0xEC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_speed_x_attack = x;
                    break;
                }
                //Y attack
                case 0xF0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_speed_y_attack = x;
                    break;
                }
                //x ground self
                case 0x14C:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_one_speed_ground_x_self = x;
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
                    m_state->m_memory->player_two_action = value_int;
                    break;
                }
                //Action counter
                case 0x20CC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    m_state->m_memory->player_two_action_counter = value_int;
                    break;
                }
                //Action frame
                case 0x8F4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_action_frame = x;
                    break;
                }
                //Invulnerable
                case 0x19EC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        m_state->m_memory->player_two_invulnerable = false;
                    }
                    else
                    {
                        m_state->m_memory->player_two_invulnerable = true;
                    }
                    break;
                }
                //Hitlag
                case 0x19BC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_hitlag_frames_left = x;
                    break;
                }
                //Hitstun
                case 0x23a0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_hitstun_frames_left = x;
                    break;
                }
                //Is charging a smash?
                case 0x2174:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    m_state->m_memory->player_two_action = value_int;
                    if(value_int == 2)
                    {
                        m_state->m_memory->player_two_charging_smash = true;
                    }
                    else
                    {
                        m_state->m_memory->player_two_charging_smash = false;
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
                    m_state->m_memory->player_two_jumps_left = value_int;
                    break;
                }
                //Is on ground?
                case 0x140:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    if(value_int == 0)
                    {
                        m_state->m_memory->player_two_on_ground = true;
                    }
                    else
                    {
                        m_state->m_memory->player_two_on_ground = false;
                    }
                    break;
                }
                //X air speed self
                case 0xE0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_speed_air_x_self = x;
                    break;
                }
                //Y air speed self
                case 0xE4:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_speed_y_self = x;
                    break;
                }
                //X attack
                case 0xEC:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_speed_x_attack = x;
                    break;
                }
                //Y attack
                case 0xF0:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_speed_y_attack = x;
                    break;
                }
                //x ground self
                case 0x14C:
                {
                    value_int = std::stoul(value.c_str(), nullptr, 16);
                    uint *val_ptr = &value_int;
                    float x = *((float*)val_ptr);
                    m_state->m_memory->player_two_speed_ground_x_self = x;
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
                m_state->m_memory->frame = value_int;
                break;
            }
            //Player 1 percent
            case 0x4530E0:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 16;
                m_state->m_memory->player_one_percent = value_int;
                break;
            }
            //Player 2 percent
            case 0x453F70:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 16;
                m_state->m_memory->player_two_percent = value_int;
                break;
            }
            //Player 1 stock
            case 0x45310E:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                m_state->m_memory->player_one_stock = value_int;

                break;
            }
            //Player 2 stock
            case 0x453F9E:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                m_state->m_memory->player_two_stock = value_int;
                break;
            }
            //Player 1 facing
            case 0x4530C0:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                bool facing = value_int >> 31;
                m_state->m_memory->player_one_facing = !facing;
                break;
            }
            //Player 2 facing
            case 0x453F50:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                bool facing = value_int >> 31;
                m_state->m_memory->player_two_facing = !facing;
                break;
            }
            //Player 1 x
            case 0x453090:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                uint *val_ptr = &value_int;
                float x = *((float*)val_ptr);
                m_state->m_memory->player_one_x = x;
                break;
            }
            //Player 2 x
            case 0x453F20:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                uint *val_ptr = &value_int;
                float x = *((float*)val_ptr);
                m_state->m_memory->player_two_x = x;
                break;
            }
            //Player 1 y
            case 0x453094:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                uint *val_ptr = &value_int;
                float x = *((float*)val_ptr);
                m_state->m_memory->player_one_y = x;
                break;
            }
            //Player 2 y
            case 0x453F24:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                uint *val_ptr = &value_int;
                float x = *((float*)val_ptr);
                m_state->m_memory->player_two_y = x;
                break;
            }
            //Player one character
            case 0x3F0E0A:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                m_state->m_memory->player_one_character = value_int;
                break;
            }
            //Player two character
            case 0x3F0E2E:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 24;
                m_state->m_memory->player_two_character = value_int;
                break;
            }
            //Menu state
            case 0x479d30:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                m_state->m_memory->menu_state = value_int;
                break;
            }
            //Stage
            case 0x4D6CAD:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                value_int = value_int >> 16;
                m_state->m_memory->stage = value_int;
                break;
            }
            //p2 cursor x
            case 0x0111826C:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                uint *val_ptr = &value_int;
                float x = *((float*)val_ptr);
                m_state->m_memory->player_two_pointer_x = x;
                break;
            }
            //p2 cursor y
            case 0x01118270:
            {
                value_int = std::stoul(value.c_str(), nullptr, 16);
                uint *val_ptr = &value_int;
                float x = *((float*)val_ptr);
                m_state->m_memory->player_two_pointer_y = x;
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
