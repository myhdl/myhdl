import os

from myhdl import Cosimulation

cmd = 'vsim -c -quiet -pli ../myhdl_vpi.dll -do cosim.do dut_dff_clkout'

def dff_clkout(clkout, q, d, clk, reset):
    os.system('vlog -quiet ../../test/verilog/dff_clkout.v')
    os.system('vlog -quiet ../../test/verilog/dut_dff_clkout.v')

    return Cosimulation(cmd, **locals())
