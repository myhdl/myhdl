import os

from myhdl import Cosimulation

cmd = "iverilog -o const_1.o " + \
      "../../test/verilog/const_1.v " + \
      "../../test/verilog/dut_const_1.v "

def const_1(q, clk):
    os.system(cmd)
    return Cosimulation("vvp -m ../myhdl.vpi const_1.o", **locals())

