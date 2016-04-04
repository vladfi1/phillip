#include <string>
#include "Controller.h"

#include <sys/types.h>  // mkfifo
#include <sys/stat.h>   // mkfifo
#include <fcntl.h>
#include <cstring>
#include <cstdlib>
#include <iostream>

#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>

Controller* Controller::m_instance = NULL;

Controller *Controller::Instance()
{
    if (!m_instance)
    {
        m_instance = new Controller();
    }
    return m_instance;
}

Controller::Controller()
{
    struct passwd *pw = getpwuid(getuid());
    std::string home_path = std::string(pw->pw_dir);
    std::string legacy_config_path = home_path + "/.dolphin-emu";
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
            pipe_path = backup_path;
            pipe_path += "/Pipes/cpu-level-11";
        }
        else
        {
            pipe_path = env_XDG_DATA_HOME;
            pipe_path += "/Pipes/cpu-level-11";
        }
    }
    else
    {
        pipe_path = legacy_config_path + "/Pipes/cpu-level-11";
    }

    m_fifo = mkfifo(pipe_path.c_str(), S_IWUSR | S_IRUSR | S_IRGRP | S_IROTH);
    std::cout << "DEBUG: Waiting for Dolphin..." << std::endl;

    if ((m_fifo = open(pipe_path.c_str(), O_WRONLY)) < 0) {
       printf("%s\n", strerror(errno));
       return;
    }
    std::cout << "DEBUG: Off to the races!" << std::endl;
}

//Hardcoded strings to send to dolphin
const std::string STRING_A = "A";
const std::string STRING_B = "B";
const std::string STRING_X = "X";
const std::string STRING_Y = "Y";
const std::string STRING_Z = "Z";
const std::string STRING_START = "START";
const std::string STRING_L = "L";
const std::string STRING_R = "R";
const std::string STRING_D_UP = "D_UP";
const std::string STRING_D_DOWN = "D_DOWN";
const std::string STRING_D_LEFT = "D_LEFT";
const std::string STRING_D_RIGHT = "D_RIGHT";
const std::string STRING_C = "C";
const std::string STRING_MAIN = "MAIN";
const std::string STRING_INVALID = "";

const std::string& buttonString(BUTTON b)
{
    switch (b)
    {
        case BUTTON_A:
        {
            return STRING_A;
        }
        case BUTTON_B:
        {
            return STRING_B;
        }
        case BUTTON_X:
        {
            return STRING_X;
        }
        case BUTTON_Y:
        {
            return STRING_Y;
        }
        case BUTTON_L:
        {
            return STRING_L;
        }
        case BUTTON_R:
        {
            return STRING_R;
        }
        case BUTTON_Z:
        {
            return STRING_Z;
        }
        case BUTTON_START:
        {
            return STRING_START;
        }
        case BUTTON_D_UP:
        {
            return STRING_D_UP;
        }
        case BUTTON_D_DOWN:
        {
            return STRING_D_DOWN;
        }
        case BUTTON_D_LEFT:
        {
            return STRING_D_LEFT;
        }
        case BUTTON_D_RIGHT:
        {
            return STRING_D_RIGHT;
        }
        case BUTTON_MAIN:
        {
            return STRING_MAIN;
        }
        case BUTTON_C:
        {
            return STRING_C;
        }
        default:
        {
            std::cout << "WARNING: Invalid button selected: " << b << std::endl;
            return STRING_INVALID;
        }
    }
}

void Controller::sendCommand(const std::string& command)
{
    //TODO: Maybe we should loop the writes until it finishes
    uint num = write(m_fifo, command.c_str(), command.length());
    if(num < command.length())
    {
        std::cout << "WARNING: Not all data written to pipe!" << std::endl;
    }
    //std::cout << "DEBUG: Command = " + command << std::endl;
}

void Controller::pressButton(BUTTON b)
{
    setButton(b, true);
}

void Controller::releaseButton(BUTTON b)
{
    setButton(b, false);
}

void Controller::setButton(BUTTON b, bool press)
{
    //TODO: we can maybe save some cycles per frame by hardcoding each string
    //  rather than assembling them here
    sendCommand((press ? "PRESS " : "RELEASE ") + buttonString(b) + "\n");
}

void Controller::pressShoulder(BUTTON b, float amount)
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
            std::cout << "WARNING: Invalid shoulder button selected: " << b << std::endl;
        }
    }
    //TODO: we can maybe save some cycles per frame by hardcoding each string
    //  rather than assembling them here
    std::string command = "SET " + button_string + " " + std::to_string(amount) + "\n";
    sendCommand(command);
}

void Controller::tiltAnalog(BUTTON b, float x, float y)
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
            std::cout << "WARNING: Invalid analog stick selected: " << b << std::endl;
        }
    }
    std::string command = "SET " + button_string + " " + std::to_string(x) +
        " " + std::to_string(y) + "\n";
    sendCommand(command);
}

void Controller::tiltAnalog(BUTTON b, float x)
{
    std::string button_string;
    switch (b)
    {
        case BUTTON_L:
        {
            button_string = STRING_L;
            break;
        }
        default:
        {
            std::cout << "WARNING: Invalid button selected!" << std::endl;
        }
    }
    std::string command = "SET " + button_string + " " + std::to_string(x) + "\n";
    sendCommand(command);
}

void Controller::emptyInput()
{
    tiltAnalog(BUTTON_MAIN, .5, .5);
    tiltAnalog(BUTTON_C, .5, .5);
    tiltAnalog(BUTTON_L, 0);
    releaseButton(BUTTON_X);
    releaseButton(BUTTON_Y);
    releaseButton(BUTTON_A);
    releaseButton(BUTTON_B);
    releaseButton(BUTTON_L);
    releaseButton(BUTTON_R);
    releaseButton(BUTTON_START);
}

// TODO: use a buffer to improve efficiency
void Controller::sendController(const ControllerState& controllerState)
{
  setButton(BUTTON_A, controllerState.buttonA());
  setButton(BUTTON_B, controllerState.buttonB());
  setButton(BUTTON_X, controllerState.buttonX());
  setButton(BUTTON_Y, controllerState.buttonY());
  setButton(BUTTON_L, controllerState.buttonL());
  setButton(BUTTON_R, controllerState.buttonR());
  
  pressShoulder(BUTTON_L, controllerState.analogL());
  pressShoulder(BUTTON_R, controllerState.analogR());
  
  tiltAnalog(BUTTON_MAIN, controllerState.mainX(), controllerState.mainY());
  tiltAnalog(BUTTON_C, controllerState.cX(), controllerState.cY());
}

