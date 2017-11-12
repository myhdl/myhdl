MyHDL co-simulation relies on Unix-style interprocess communication.
To run co-simulation on Windows, compile and use all tools involved
(including Python itself) on a Unix-like environment for Windows, such
as cygwin.

For co-simulation with Verilaor, a working Verilator installation is
required, so that the command 'verilator' is available.  See
http://www.veripool.org/verilator

The examples were verified with Verilator 3.914.

To speed up compile times, you may also want to install ccache, and point
Verilator to it; see the Verilator documentation.

Run the Makefile by typing 'make'. This will create the examples.  The
examples run Verilator, then run GCC compile the design.

Verilator does not have traditional testbench support, therefore the
examples here assume that MyHDL is always the testbench, and a Verilated
model is underneath that MyHDL testbench. The design under test is
Verilated directly.  No wrapper is required as with other simulators (no
'$to_myhdl' nor '$from_myhdl' tasks). Please see the manual.

For smaller designs be aware a great deal of CPU time will be spent in
passing information between Verilator and MyHDL, versus inside the RTL
simulation itself. If performance is critical, you may want to run a
profile and possibly hand write a standalone sim_main.cpp.
