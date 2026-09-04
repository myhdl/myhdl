all: iverilog ghdl 

vcom:
	py.test --sim vcom

iverilog:
	py.test --sim iverilog

ghdl:
	py.test --sim ghdl

clean:
	- rm *.o *.out *.v *.vhd *.pyc *~ *.vcd* *.log *_ghdl

gitclean:
	git clean -dfx
