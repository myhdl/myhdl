A working Icarus installation is required, so that the commands
'iverilog' and 'vvp' are available.

Run the Makefile by typing 'make'. This should generate a 'myhdl.vpi'
PLI module. Install it in an appropriate location, where 'vvp' can
find it. Note that you can use the '-m' flag to vvp to specify the PLI
module path.

For co-simulation with MyHDL, 'vvp' should be run with the 'myhdl.vpi'
PLI module, and the Verilog code should contain the appropriate calls
to the '$to_myhdl' and 'from_myhdl' tasks.

The 'myhdl.vpi' module was developed and verified with Icarus 0.7.
