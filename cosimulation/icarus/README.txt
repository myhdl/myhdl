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

Between snapshot 20030518 (used in MyHDL 0.3), and 2001009, the
Icarus scheduler has been improved. This requires a small update
of myhdl.c. The current version is supposed to work with recent
snapshot - the older version is availabele in myhdl.c.20030518.
