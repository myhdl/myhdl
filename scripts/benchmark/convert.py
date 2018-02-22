from __future__ import absolute_import
import myhdl
from myhdl import *

from test_lfsr24 import test_lfsr24
from test_randgen import test_randgen
from test_longdiv import test_longdiv
from test_timer import test_timer
from timer import timer_sig, timer_var
from test_findmax import test_findmax

toVerilog(test_lfsr24)
toVHDL(test_lfsr24)

toVerilog(test_randgen)
toVHDL(test_randgen)

toVerilog(test_longdiv)
toVHDL(test_longdiv)

toVerilog(test_timer, timer_var)
toVHDL(test_timer, timer_var)

toVerilog(test_findmax)
toVHDL(test_findmax)
