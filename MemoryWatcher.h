#ifndef MEMORY_WATCHER_H
#define MEMORY_WATCHER_H

#include "GameState.h"

class MemoryWatcher
{

public:

    MemoryWatcher();

    //Returns true if the memory read was an updated frame count, false otherwise
    //Blocking call
    bool ReadMemory(GameMemory& memory);

private:
    //File descriptor
    int m_file;

};

#endif
