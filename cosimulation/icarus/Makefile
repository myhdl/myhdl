all: myhdl.vpi

myhdl.vpi: myhdl.c myhdl_table.c 
	iverilog-vpi myhdl.c myhdl_table.c

clean:
	-rm *.o *.vpi
