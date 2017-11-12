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
                 # Source code
                 " ../../test/verilog/dff.v"
                 # Signal connections (and this file includes verilator_myhdl_main.cpp and myhdl.cpp)
                 " obj_dir/Vdff__myhdl.cpp"
                 "")

make_cmd = ("make"
            # Parallel
            " -j"
            # cd into obj_dir
            " -C obj_dir"
            # Default compile flags
            " OPT_FAST=-O"
            # Top level needs to know name of the model
            " USER_CPPFLAGS='-I../.. -DMODEL=Vdff'"
            # Run the model's make
            " -f Vdff.mk"
            "")

run_cmd = "obj_dir/Vdff"

def dff(q, d, clk, reset):
    cmd = ((os.getenv("VERILATOR_ROOT")+"/bin/verilator" if os.getenv("VERILATOR_ROOT") else "verilator")
           + verilator_flags + " " + verilog_flags)
    os.system(cmd)  # TODO: optional print of command, and error checking here?

    cmd = "../verilator_myhdl_wrapper obj_dir/Vdff.h obj_dir/Vdff__myhdl.cpp"
    os.system(cmd)  # TODO: optional print of command, and error checking here?

    os.system(make_cmd)  # TODO: optional print of command, and error checking here?

    return Cosimulation(run_cmd, **locals())
