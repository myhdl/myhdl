import os

from myhdl import Cosimulation

cmd = "iverilog -o dff " + \
      "../../test/verilog/dff.v " + \
      "../../test/verilog/dut_dff.v "
      
def dff(q, d, clk, reset):
    os.system(cmd)
    return Cosimulation("vvp -m ../myhdl.vpi dff", **locals())
               
