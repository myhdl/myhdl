# could add to CFLAGS to turn on warnings if you are using gcc
WARNS=-Wall

# change this path to point to the pli include files directory for cver
INCS=-I $(shell dirname `which vsim`)/../include

# maybe want -O<something> and/or -g

# 32bit for Altera ASE/PE on Ubuntu Natty Narwhal
CFLAGS= -fPIC -Wall -g -m32 $(INCS) -fno-stack-protector
LFLAGS= -G -shared -export-dynamic -melf_i386

# 64bit for SE
#CFLAGS= -fPIC -Wall -c -g $(INCS)
#LFLAGS= -shared -E

# change to your compiler 
CC=gcc 

all: myhdl_vpi.so

myhdl_vpi.o:	myhdl_vpi.c 
	$(CC) $(CFLAGS) -c myhdl_vpi.c

# make rules for dynamic libaries
myhdl_vpi.so:	myhdl_vpi.o
	$(LD) $(LFLAGS) myhdl_vpi.o -o myhdl_vpi.so

clean:
	-rm *.o *.so
 
.PHONY: test
test: myhdl_vpi.so
	rm -rf test/work
	cd test && vlib work && python test_all.py
