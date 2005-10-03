import os

from myhdl import Cosimulation

cmd = "iverilog -o inc.o -Dn=%s " + \
      "../../test/verilog/inc.v " + \
      "../../test/verilog/dut_inc.v "
      
def inc(count, enable, clock, reset, n):
    os.system(cmd % n)
    return Cosimulation("vvp -m ../myhdl.vpi inc.o", **locals())
               
