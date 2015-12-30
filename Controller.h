#ifndef _Controller
#define _Controller

#pragma once

#include <string>

class Controller {
public:
    enum BUTTON {
        BUTTON_A,
        BUTTON_B,
        BUTTON_X,
        BUTTON_Y,
        BUTTON_Z,
        BUTTON_L,
        BUTTON_R,
        BUTTON_START,
        BUTTON_D_UP,
        BUTTON_D_DOWN,
        BUTTON_D_LEFT,
        BUTTON_D_RIGHT,
        BUTTON_MAIN,
        BUTTON_C
    };

    static Controller *Instance();

    void pressButton(BUTTON b);
    void releaseButton(BUTTON b);
    // Analog values are clamped to [0, 1].
    void pressShoulder(BUTTON b, double amount);
    void tiltAnalog(BUTTON B, double x, double y);
    void tiltAnalog(BUTTON B, double x);

    //Press no buttons, move sticks back to neutral
    void emptyInput();

private:
    Controller();

    static Controller *m_instance;
    int m_fifo;
    //Hardcoded strings to send to dolphin
    std::string STRING_A = "A";
    std::string STRING_B = "B";
    std::string STRING_X = "X";
    std::string STRING_Y = "Y";
    std::string STRING_Z = "Z";
    std::string STRING_START = "START";
    std::string STRING_L = "L";
    std::string STRING_R = "R";
    std::string STRING_D_UP = "D_UP";
    std::string STRING_D_DOWN = "D_DOWN";
    std::string STRING_D_LEFT = "D_LEFT";
    std::string STRING_D_RIGHT = "D_RIGHT";
    std::string STRING_C = "C";
    std::string STRING_MAIN = "MAIN";
};

#endif
