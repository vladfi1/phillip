CC=g++
CFLAGS=-g -c -Wall -std=gnu++11
LDFLAGS=-g -Wall -std=gnu++11

SOURCES=cpu.cpp Controller.cpp GameState.cpp MemoryWatcher.cpp
GOALS=Goals/*.cpp
STRATS=Strategies/*.cpp
TACTICS=Tactics/*.cpp
CHAINS=Chains/*.cpp

EXECUTABLE=cpu

all: main
	$(CC) $(LDFLAGS) *.o -o $(EXECUTABLE)

main:
	$(CC) $(CFLAGS) $(SOURCES)

goals:
	$(CC) $(CFLAGS) $(GOALS)

strats:
	$(CC) $(CFLAGS) $(STRATS)

tactics:
	$(CC) $(CFLAGS) $(TACTICS)

chains:
	$(CC) $(CFLAGS) $(CHAINS)

clean:
	rm -f *.o */*.o *.d */*.d cpu
