all:  vlog vcom 

ghdl:
	py.test --sim ghdl

vlog:
	py.test --sim vlog

vcom:
	py.test --sim vcom

iverilog:
	py.test --sim iverilog

cver:
	py.test --sim cver

clean:
	- rm *.o *.out *.v *.vhd *.pyc *~ *.vcd* *.log *_ghdl

gitclean:
	git clean -dfx
