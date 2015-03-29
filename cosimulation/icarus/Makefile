all: myhdl.vpi

myhdl.vpi: myhdl.c myhdl_table.c 
	iverilog-vpi myhdl.c myhdl_table.c

.PHONY: test
test: myhdl.vpi
	make -C test

clean:
	-rm *.o *.vpi
