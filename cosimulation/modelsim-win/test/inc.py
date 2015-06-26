import os

from myhdl import Cosimulation

cmd = 'vsim -c -quiet -pli ../myhdl_vpi.so -do cosim.do dut_inc'

def inc(count, enable, clock, reset, n):
    os.system('vlog -quiet +define+n=%s ../../test/verilog/inc.v' % (n))
    os.system('vlog -quiet +define+n=%s ../../test/verilog/dut_inc.v' % (n)) 

    return Cosimulation(cmd, **locals())
               
