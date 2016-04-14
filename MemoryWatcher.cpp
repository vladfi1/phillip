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

using namespace std;

// TODO: pass in watcher location
MemoryWatcher::MemoryWatcher()
{
    struct passwd *pw = getpwuid(getuid());
    string home_path = string(pw->pw_dir);
    string legacy_config_path = home_path + "/.dolphin-emu";
    string mem_watcher_path;

    struct stat buffer;
    if(stat(legacy_config_path.c_str(), &buffer) != 0)
    {
        //If the legacy app path is not present, see if the new one is
        const char *env_XDG_DATA_HOME = getenv("XDG_DATA_HOME");
        if(env_XDG_DATA_HOME == NULL)
        {
            //Try $HOME/.local/share next
            string backup_path = home_path + "/.local/share/dolphin-emu";
            if(stat(backup_path.c_str(), &buffer) != 0)
            {
                cout << "ERROR: $XDG_DATA_HOME was empty and so was $HOME/.dolphin-emu and $HOME/.local/share/dolphin-emu " \
                    "Are you sure Dolphin is installed? Make sure it is, and then run the CPU again." << endl;
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

void ReadPlayer(PlayerMemory& player, uint ptr_int, uint value_int)
{
    switch(ptr_int)
    {
        //Action
        case 0x70:
        {
            player.action = value_int;
            break;
        }
        //Action counter
        case 0x20CC:
        {
            player.action_counter = value_int;
            break;
        }
        //Action frame
        case 0x8F4:
        {
            player.action_frame = asFloat(value_int);
            break;
        }
        //Invulnerable
        case 0x19EC:
        {
            if(value_int == 0)
            {
                player.invulnerable = false;
            }
            else
            {
                player.invulnerable = true;
            }
            break;
        }
        //Hitlag
        case 0x19BC:
        {
            player.hitlag_frames_left = asFloat(value_int);
            break;
        }
        //Hitstun
        case 0x23a0:
        {
            player.hitstun_frames_left = asFloat(value_int);
            break;
        }
        //Is charging a smash?
        case 0x2174:
        {
            player.action = value_int;
            if(value_int == 2)
            {
                player.charging_smash = true;
            }
            else
            {
                player.charging_smash = false;
            }
            break;
        }
        //Jumps remaining
        case 0x19C8:
        {
            value_int = value_int >> 24;
            //TODO: This won't work for characters with multiple jumps
            if(value_int > 1)
            {
                value_int = 0;
            }
            player.jumps_left = value_int;
            break;
        }
        //Is on ground?
        case 0x140:
        {
            if(value_int == 0)
            {
                player.on_ground = true;
            }
            else
            {
                player.on_ground = false;
            }
            break;
        }
        //X air speed self
        case 0xE0:
        {
            player.speed_air_x_self = asFloat(value_int);
            break;
        }
        //Y air speed self
        case 0xE4:
        {
            player.speed_y_self = asFloat(value_int);
            break;
        }
        //X attack
        case 0xEC:
        {
            player.speed_x_attack = asFloat(value_int);
            break;
        }
        //Y attack
        case 0xF0:
        {
            player.speed_y_attack = asFloat(value_int);
            break;
        }
        //x ground self
        case 0x14C:
        {
            player.speed_ground_x_self = asFloat(value_int);
            break;
        }
        default:
        {
            cout << "WARNING: Got an unexpected memory pointer: " << ptr_int << endl;
        }
    }
}

bool MemoryWatcher::ReadMemory(GameMemory& memory)
{
    char buf[128];
    memset(buf, '\0', 128);

    struct sockaddr remaddr;
    socklen_t addr_len;
    recvfrom(m_file, buf, sizeof(buf), 0, &remaddr, &addr_len);
    stringstream ss(buf);
    string region, value;

    getline(ss, region, '\n');
    getline(ss, value, '\n');
    uint value_int = stoul(value.c_str(), nullptr, 16);

    //Is this a followed pointer?
    size_t found = region.find(" ");
    if(found != string::npos)
    {
        string ptr = region.substr(found+1);
        string base = region.substr(0, found);
        uint ptr_int = stoul(ptr.c_str(), nullptr, 16);
        uint base_int = stoul(base.c_str(), nullptr, 16);

        switch(base_int)
        {
            //Player one
            case 0x453130:
            {
                ReadPlayer(memory.player_one, ptr_int, value_int);
                break;
            }
            //Player two
            case 0x453FC0:
            {
                ReadPlayer(memory.player_two, ptr_int, value_int);
                break;
            }
            default:
            {
                cout << "WARNING: Got an unexpected memory base pointer: " << base_int << endl;
            }
        }
    }
    //If not, it's a direct pointer
    else
    {
        uint region_int = stoul(region.c_str(), nullptr, 16);
        switch(region_int)
        {
            //Frame
            case 0x479D60:
            {
                memory.frame = value_int;
                break;
            }
            //Player 1 percent
            case 0x4530E0:
            {
                memory.player_one.percent = value_int >> 16;
                break;
            }
            //Player 2 percent
            case 0x453F70:
            {
                memory.player_two.percent = value_int >> 16;
                break;
            }
            //Player 1 stock
            case 0x45310E:
            {
                memory.player_one.stock = value_int >> 24;
                break;
            }
            //Player 2 stock
            case 0x453F9E:
            {
                memory.player_two.stock = value_int >> 24;
                break;
            }
            //Player 1 facing
            case 0x4530C0:
            {
                bool facing = value_int >> 31;
                memory.player_one.facing = !facing;
                break;
            }
            //Player 2 facing
            case 0x453F50:
            {
                bool facing = value_int >> 31;
                memory.player_two.facing = !facing;
                break;
            }
            //Player 1 x
            case 0x453090:
            {
                memory.player_one.x = asFloat(value_int);
                break;
            }
            //Player 2 x
            case 0x453F20:
            {
                memory.player_two.x = asFloat(value_int);
                break;
            }
            //Player 1 y
            case 0x453094:
            {
                memory.player_one.y = asFloat(value_int);
                break;
            }
            //Player 2 y
            case 0x453F24:
            {
                memory.player_two.y = asFloat(value_int);
                break;
            }
            //Player one character
            case 0x3F0E0A:
            {
                memory.player_one.character = value_int >> 24;
                break;
            }
            //Player two character
            case 0x3F0E2E:
            {
                memory.player_two.character = value_int >> 24;
                break;
            }
            //Menu state
            case 0x479d30:
            {
                memory.menu_state = value_int;
                cout << value_int << endl;
                break;
            }
            //Stage
            case 0x4D6CAD:
            {
                memory.stage = value_int >> 16;
                cout << value_int << endl;
                break;
            }
            //p2 cursor x
            case 0x0111826C:
            {
                memory.player_two_pointer_x = asFloat(value_int);
                break;
            }
            //p2 cursor y
            case 0x01118270:
            {
                memory.player_two_pointer_y = asFloat(value_int);
                break;
            }
            case 0x003F0E08:
            {
                cout << hex << "P1: " << value_int << endl;
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
