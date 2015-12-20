#include <cmath>
#include <typeinfo>

#include "ShineCombo.h"
#include "../Chains/Waveshine.h"

ShineCombo::ShineCombo()
{
    m_chain = NULL;
}

ShineCombo::~ShineCombo()
{
    delete m_chain;
}

void ShineCombo::DetermineChain()
{
    CreateChain(Waveshine);
    m_chain->PressButtons();
}
