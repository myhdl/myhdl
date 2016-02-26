all: vcom 

vcom:
	py.test --sim vcom

ghdl:
	py.test --sim ghdl

clean:
	- rm *.o *.out *.v *.vhd *.pyc *~ *.vcd* *.log *_ghdl

gitclean:
	git clean -dfx
