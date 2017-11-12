all: myhdl.vpi

myhdl.vpi: myhdl.c myhdl_table.c 
	iverilog-vpi myhdl.c myhdl_table.c

.PHONY: test
test: myhdl.vpi
	cd test && python test_all.py

clean:
	-rm *.o *.vpi
