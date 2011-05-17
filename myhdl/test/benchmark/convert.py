from myhdl import *

from test_lfsr24 import test_lfsr24
from test_randgen import test_randgen
from test_longdiv import test_longdiv

toVerilog(test_lfsr24)
toVHDL(test_lfsr24)

toVerilog(test_randgen)
toVHDL(test_randgen)

toVerilog(test_longdiv)
toVHDL(test_longdiv)

