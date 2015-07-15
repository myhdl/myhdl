# This makefile assumes that 32bit Modelsim is installed.
# If you have a 64 bit version, run 'ARCH=64 make'
ARCH?=32
CFLAGS_32= -m32
CFLAGS_64= -m64

# Guess include dir based on location of vsim
INCS=-I $(shell dirname `which vsim`)/../include
CFLAGS= -Wall -shared -BSymbolic -fPIC $(CFLAGS_$(ARCH)) $(INCS)

VSIM_VERSION=$(shell vsim -version 2>/dev/null; echo $$?)


all: myhdl_vpi.so

myhdl_vpi.so: myhdl_vpi.c
	$(info Compiling $(ARCH)bit vpi lib for "$(VSIM_VERSION)") 
	$(info )
	$(CC) $(CFLAGS) -o $@ $?

clean:
	@rm -f myhdl_vpi.so
 
.PHONY: test
test: myhdl_vpi.so
	rm -rf test/work
	cd test && vlib work && python test_all.py
