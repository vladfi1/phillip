#include "Nothing.h"

void Nothing::PressButtons()
{
    //Just send this once. Not every frame
    //Reset the controller blank
    if(!m_reset)
    {
        m_controller->emptyInput();
        m_reset = true;
    }
}

//We're always interruptible during nothing
bool Nothing::IsInterruptible()
{
    return true;
}

Nothing::Nothing()
{
    m_reset = false;
}

Nothing::~Nothing()
{
}
