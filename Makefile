all:
	g++ cpu.cpp -std=c++11 -lxdo -o cpu

clean:
	rm cpu
