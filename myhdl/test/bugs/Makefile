all: vlog vcom 


vlog:
	py.test --sim vlog

vcom:
	py.test --sim vcom


GHDL:
	py.test --sim GHDL

icarus:
	py.test --sim icarus

cver:
	py.test --sim cver

clean:
	- rm *.o *.out *.v *.vhd *.pyc *~ *.vcd* *.log *_ghdl
