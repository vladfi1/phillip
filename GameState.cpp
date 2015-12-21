#include "GameState.h"

#include <string>

GameState* GameState::m_instance = NULL;

GameState *GameState::Instance()
{
    if (!m_instance)
    {
        m_instance = new GameState();
    }
    return m_instance;
}

double GameState::getStageEdgePosition()
{
    double edge_position = 100;
    switch(m_memory->stage)
    {
        case BATTLEFIELD:
        {
            edge_position = 71.3078536987;
            break;
        }
        case FINAL_DESTINATION:
        {
            edge_position = 88.4735488892;
            break;
        }
        case DREAMLAND:
        {
            edge_position = 80.1791534424;
            break;
        }
        case FOUNTAIN_OF_DREAMS:
        {
            edge_position = 66.2554016113;
            break;
        }
    }
    return edge_position;
}

GameState::GameState()
{

}
