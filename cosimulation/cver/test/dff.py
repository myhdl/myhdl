import os

from myhdl import Cosimulation

cmd = "cver -q +loadvpi=../myhdl_vpi:vpi_compat_bootstrap " + \
      "../../test/verilog/dff.v " + \
      "../../test/verilog/dut_dff.v "
      
def dff(q, d, clk, reset):
    return Cosimulation(cmd, **locals())
               
