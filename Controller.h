#ifndef _Controller
#define _Controller

#pragma once

#include <string>

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

const std::string& getString(BUTTON);

struct ControllerState {
  bool buttonA, buttonB, buttonX, buttonY, buttonL, buttonR;
  
  float analogL, analogR;
  
  float mainX, mainY;
  float cX, cY;
  
  void reset();
  
  ControllerState();
};

class Controller {
public:
    Controller(const std::string& pipeName);

    void pressButton(BUTTON b);
    void releaseButton(BUTTON b);
    void setButton(BUTTON b, bool press);
    
    // Analog values are clamped to [0, 1].
    void pressShoulder(BUTTON b, float amount);
    void tiltAnalog(BUTTON B, float x, float y);
    void tiltAnalog(BUTTON B, float x);

    //Press no buttons, move sticks back to neutral
    void emptyInput();
    
    void sendState(const ControllerState& controllerState);

private:
    void sendCommand(const std::string& command);
    
    int m_fifo;
    
};

#endif
