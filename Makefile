all:
	g++ cpu.cpp Controller.cpp -g -Wall -std=c++11 -lxdo -o cpu

clean:
	rm cpu
