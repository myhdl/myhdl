import os

from myhdl import Cosimulation

cmd = "cver -q +loadvpi=../myhdl_vpi:vpi_compat_bootstrap +define+n=%s " + \
      "../../test/verilog/inc.v " + \
      "../../test/verilog/dut_inc.v "

def inc(count, enable, clock, reset, n):
    return Cosimulation(cmd % n, **locals())
               
