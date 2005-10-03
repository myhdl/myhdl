import os
import os.path as path

from myhdl import Cosimulation

cmd = "iverilog -o dff_clkout.o " + \
      "../../test/verilog/dff_clkout.v " + \
      "../../test/verilog/dut_dff_clkout.v "
      
def dff_clkout(clkout, q, d, clk, reset):
    if path.exists("dff_clkout"):
        os.remove("dff_clkout")
    os.system(cmd)
    return Cosimulation("vvp -m ../myhdl.vpi dff_clkout.o", **locals())
               
