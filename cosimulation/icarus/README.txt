MyHDL co-simulation relies on Unix-style interprocess communication.
To run co-simulation on Windows, compile and use all tools involved
(including Python itself) on a Unix-like environment for Windows, such
as cygwin.

For co-simulation with Icarus, a working Icarus installation is required,
so that the commands 'iverilog' and 'vvp' are available.

Run the Makefile by typing 'make'. This should generate a 'myhdl.vpi'
PLI module. Install it in an appropriate location, where 'vvp' can
find it. Note that you can use the '-m' flag to vvp to specify the PLI
module path.

To test whether it works, go to the 'test' subdirectory and run the
tests with 'python test_all.py'.

For co-simulation with MyHDL, 'vvp' should be run with the 'myhdl.vpi'
PLI module, and the Verilog code should contain the appropriate calls
to the '$to_myhdl' and 'from_myhdl' tasks.

The 'myhdl.vpi' module was developed and verified with Icarus 0.7.

Between snapshot 20030518 (used in MyHDL 0.3), and 20031009, the
Icarus scheduler has been improved. This requires a small update of
myhdl.c. The current version is supposed to work with recent snapshots
- the older version is available in myhdl_20030518.c
