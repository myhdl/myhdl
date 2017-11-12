import os
import sys

from myhdl import Cosimulation

verilator_flags = (""
                   # Generate C++ with VPI in executable form
                   " -cc --vpi --exe"
                   # Optimize more
                   #" -O2 -x-assign 0"
                   # Warn abount lint issues; may not want this on less solid designs
                   #" -Wall"
                   # Make waveforms
                   #" --trace"
                   # Check SystemVerilog assertions
                   #" --assert"
                   # Generate coverage analysis
                   #" --coverage"
                   # Run Verilator in debug mode
                   #" --debug"
                   "")

verilog_flags = (""
                 # Set "n" parameter based on the size passed from the test
                 " -Gn=%s"
                 # Source code
                 " ../../test/verilog/inc.v"
                 # Signal connections (and this file includes verilator_myhdl_main.cpp and myhdl.cpp)
                 " obj_dir/Vinc__myhdl.cpp"
                 "")

make_cmd = ("make"
            # Parallel
            " -j"
            # cd into obj_dir
            " -C obj_dir"
            # Default compile flags
            " OPT_FAST=-O"
            # Top level needs to know name of the model
            " USER_CPPFLAGS='-I../.. -DMODEL=Vinc'"
            # Run the model's make
            " -f Vinc.mk"
            "")

run_cmd = "obj_dir/Vinc"

######################################################################

def inc(count, enable, clock, reset, n):
    cmd = ((os.getenv("VERILATOR_ROOT")+"/bin/verilator" if os.getenv("VERILATOR_ROOT") else "verilator")
           + verilator_flags
           + " " + (verilog_flags % n))
    os.system(cmd)  # TODO: error checking here?

    cmd = "../verilator_myhdl_wrapper obj_dir/Vinc.h obj_dir/Vinc__myhdl.cpp"
    os.system(cmd)  # TODO: error checking here?

    os.system(make_cmd)  # TODO: error checking here?

    return Cosimulation(run_cmd, **locals())
