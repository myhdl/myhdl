import os

from myhdl import Cosimulation

cmd = "cver -q +loadvpi=../myhdl_vpi:vpi_compat_bootstrap +define+width=%s " + \
      "../../test/verilog/bin2gray.v " + \
      "../../test/verilog/dut_bin2gray.v "
       
def bin2gray(B, G, width):
    return Cosimulation(cmd % width, B=B, G=G)
               

