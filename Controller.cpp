#include <string>
#include "Controller.h"

#include <sys/types.h>  // mkfifo
#include <sys/stat.h>   // mkfifo
#include <fcntl.h>
#include <cstring>
#include <iostream>

#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

Controller::Controller()
{
    //TODO: unhardcode the home folder
    m_fifo = mkfifo("/home/altf4/.dolphin-emu/Pipes/cpu-level-11", S_IWUSR | S_IRUSR | S_IRGRP | S_IROTH);
    std::cout << "DEBUG: Waiting for Dolphin..." << std::endl;

    if ((m_fifo = open("/home/altf4/.dolphin-emu/Pipes/cpu-level-11", O_WRONLY)) < 0) {
       printf("%s\n", strerror(errno));
       return;
    }

}

Controller::~Controller()
{

}

void Controller::pressButton(BUTTON b)
{
    std::string button_string;
    switch (b)
    {
        case BUTTON_A:
        {
            button_string = STRING_A;
            break;
        }
        case BUTTON_B:
        {
            button_string = STRING_B;
            break;
        }
        case BUTTON_X:
        {
            button_string = STRING_X;
            break;
        }
        case BUTTON_Y:
        {
            button_string = STRING_Y;
            break;
        }
        case BUTTON_L:
        {
            button_string = STRING_L;
            break;
        }
        case BUTTON_R:
        {
            button_string = STRING_R;
            break;
        }
        case BUTTON_Z:
        {
            button_string = STRING_Z;
            break;
        }
        case BUTTON_START:
        {
            button_string = STRING_START;
            break;
        }
        case BUTTON_D_UP:
        {
            button_string = STRING_D_UP;
            break;
        }
        case BUTTON_D_DOWN:
        {
            button_string = STRING_D_DOWN;
            break;
        }
        case BUTTON_D_LEFT:
        {
            button_string = STRING_D_LEFT;
            break;
        }
        case BUTTON_D_RIGHT:
        {
            button_string = STRING_D_RIGHT;
            break;
        }
        case BUTTON_MAIN:
        {
            button_string = STRING_MAIN;
            break;
        }
        case BUTTON_C:
        {
            button_string = STRING_C;
            break;
        }
        default:
        {
            std::cout << "WARNING: Invalid button selected!" << std::endl;
        }
    }
    //TODO: we can maybe same some cycles per frame by hardcoding each string
    //  rather than assembling them here
    std::string command = "PRESS " + button_string + "\n";
    //TODO: Maybe we should loop the writes until it finishes
    uint num = write(m_fifo, command.c_str(), command.length());
    if(num < command.length())
    {
        std::cout << "WARNING: Not all data written to pipe!" << std::endl;
    }
    std::cout << "DEBUG: Command = " + command << std::endl;
}

void Controller::releaseButton(BUTTON b)
{
    std::string button_string;
    switch (b)
    {
        case BUTTON_A:
        {
            button_string = STRING_A;
            break;
        }
        case BUTTON_B:
        {
            button_string = STRING_B;
            break;
        }
        case BUTTON_X:
        {
            button_string = STRING_X;
            break;
        }
        case BUTTON_Y:
        {
            button_string = STRING_Y;
            break;
        }
        case BUTTON_L:
        {
            button_string = STRING_L;
            break;
        }
        case BUTTON_R:
        {
            button_string = STRING_R;
            break;
        }
        case BUTTON_Z:
        {
            button_string = STRING_Z;
            break;
        }
        case BUTTON_START:
        {
            button_string = STRING_START;
            break;
        }
        case BUTTON_D_UP:
        {
            button_string = STRING_D_UP;
            break;
        }
        case BUTTON_D_DOWN:
        {
            button_string = STRING_D_DOWN;
            break;
        }
        case BUTTON_D_LEFT:
        {
            button_string = STRING_D_LEFT;
            break;
        }
        case BUTTON_D_RIGHT:
        {
            button_string = STRING_D_RIGHT;
            break;
        }
        case BUTTON_MAIN:
        {
            button_string = STRING_MAIN;
            break;
        }
        case BUTTON_C:
        {
            button_string = STRING_C;
            break;
        }
        default:
        {
            std::cout << "WARNING: Invalid button selected!" << std::endl;
        }
    }
    //TODO: we can maybe same some cycles per frame by hardcoding each string
    //  rather than assembling them here
    std::string command = "RELEASE " + button_string + "\n";
    uint num = write(m_fifo, command.c_str(), command.length());
    if(num < command.length())
    {
        std::cout << "WARNING: Not all data written to pipe!" << std::endl;
    }
    std::cout << "DEBUG: Command = " + command << std::endl;

}

void Controller::pressShoulder(BUTTON b, double amount)
{
    std::string button_string;
    switch (b)
    {
        case BUTTON_L:
        {
            button_string = STRING_L;
            break;
        }
        case BUTTON_R:
        {
            button_string = STRING_R;
            break;
        }
        default:
        {
            std::cout << "WARNING: Invalid button selected!" << std::endl;
        }
    }
    //TODO: we can maybe same some cycles per frame by hardcoding each string
    //  rather than assembling them here
    std::string command = "SET " + button_string + " " + std::to_string(amount) + "\n";
    uint num = write(m_fifo, command.c_str(), command.length());
    if(num < command.length())
    {
        std::cout << "WARNING: Not all data written to pipe!" << std::endl;
    }
    std::cout << "DEBUG: Command = " + command << std::endl;
}

void Controller::tiltAnalog(BUTTON b, double x, double y)
{
    std::string button_string;
    switch (b)
    {
        case BUTTON_MAIN:
        {
            button_string = STRING_MAIN;
            break;
        }
        case BUTTON_C:
        {
            button_string = STRING_C;
            break;
        }
        default:
        {
            std::cout << "WARNING: Invalid button selected!" << std::endl;
        }
    }
    //TODO: we can maybe same some cycles per frame by hardcoding each string
    //  rather than assembling them here
    std::string command = "SET " + button_string + " " + std::to_string(x) +
        " " + std::to_string(y) + "\n";
    uint num = write(m_fifo, command.c_str(), command.length());
    if(num < command.length())
    {
        std::cout << "WARNING: Not all data written to pipe!" << std::endl;
    }
    std::cout << "DEBUG: Command = " + command << std::endl;
}
