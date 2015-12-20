#include <cmath>
#include <typeinfo>

#include "Wait.h"
#include "../Chains/Nothing.h"

Wait::Wait()
{
    m_chain = NULL;
}

Wait::~Wait()
{
    delete m_chain;
}

void Wait::DetermineChain()
{
    CreateChain(Nothing);
    m_chain->PressButtons();
}
