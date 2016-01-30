.PHONY: all general toVerilog2 toVHDL toVerilog

all: general toVerilog2 toVHDL toVerilog

general:
	cd general; py.test --sim ghdl; py.test --sim iverilog 

toVerilog2:
	cd toVerilog2; py.test --sim iverilog 

toVHDL:
	cd toVHDL; py.test --sim ghdl 

toVerilog: 
	cd toVerilog; py.test --sim iverilog 

gitclean:
	git clean -dfx    
    
