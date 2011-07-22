# could add to CFLAGS to turn on warnings if you are using gcc
WARNS=-Wall

# change this path to point to the pli include files directory for cver
INCS=-I "' Path to Modelsim exe "'

# maybe want -O<something> and/or -g

# 32bit for Altera PE
#CFLAGS= -fPIC -Wall -g -m32 $(INCS)
#LFLAGS= -G -shared -export-dynamic -melf_i386

# 64bit for SE
CFLAGS= -fPIC -Wall -c -g $(INCS)
LFLAGS= -shared -E #-melf_i386

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
 