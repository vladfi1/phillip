CC=g++
CFLAGS=-g -c -Wall -std=gnu++11
LDFLAGS=-g -Wall -std=gnu++11

SOURCES=cpu.cpp Controller.cpp
GOALS=Goals/KillOpponent.cpp
STRATS=Strategies/Bait.cpp
TACTICS=Tactics/CloseDistance.cpp Tactics/Wait.cpp Tactics/Parry.cpp
CHAINS=Chains/SHDL.cpp Chains/Multishine.cpp Chains/Jog.cpp Chains/Nothing.cpp Chains/Powershield.cpp

EXECUTABLE=cpu

all: goals strats tactics chains main
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
