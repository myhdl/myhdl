import os

from myhdl import Cosimulation

cmd = 'vsim -c -quiet -pli ../myhdl_vpi.dll -do cosim.do dut_bin2gray'

def bin2gray(B, G, width):
    os.system('vlog -quiet +define+width=%s ../../test/verilog/bin2gray.v' % (width))
    os.system('vlog -quiet +define+width=%s ../../test/verilog/dut_bin2gray.v' % (width))

    return Cosimulation(cmd, B=B, G=G)
