import os

from myhdl import Cosimulation

cmd = 'vsim -c -quiet -pli ../myhdl_vpi.so -do cosim.do dut_dff'
      
def dff(q, d, clk, reset):
    os.system('vlog -quiet ../../test/verilog/dff.v')
    os.system('vlog -quiet ../../test/verilog/dut_dff.v') 

    return Cosimulation(cmd, **locals())
               
