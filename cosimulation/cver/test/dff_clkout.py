import os
import os.path as path

from myhdl import Cosimulation

cmd = "cver -q +loadvpi=../myhdl_vpi:vpi_compat_bootstrap " + \
      "../../test/verilog/dff_clkout.v " + \
      "../../test/verilog/dut_dff_clkout.v "
      
def dff_clkout(clkout, q, d, clk, reset):
    return Cosimulation(cmd, **locals())
               
