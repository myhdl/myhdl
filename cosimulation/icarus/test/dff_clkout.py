import os

from myhdl import Cosimulation

cmd = "iverilog -o dff_clkout " + \
      "../../test/verilog/dff_clkout.v " + \
      "../../test/verilog/dut_dff_clkout.v "
      
def dff_clkout(clkout, q, d, clk, reset):
    os.system("rm dff_clkout")
    os.system(cmd)
    return Cosimulation("vvp -m ../myhdl.vpi dff_clkout", **locals())
               
