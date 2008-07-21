MyHDL co-simulation relies on Unix-style interprocess communication.
To run co-simulation on Windows, compile and use all tools involved
(including Python itself) on a Unix-like environment for Windows, such
as cygwin.

For co-simulation with cver, the following is required:
  * a working cver installation
  * a 'myhdl_vpi.so' file, generated from 'myhdl_vpi.c'

For Linux, a makefile 'makefile.lnx' is provided to generate 'myhdl_vpi.so'. 
However, you will have to edit the makefile to point to the correct
pli include files for cver. See the makefile for instructions.

To test whether it works, go to the 'test' subdirectory and run the
tests with 'python test_all.py'. 

For co-simulation with MyHDL, 'cver' should be run with the 'myhdl_vpi.so'
PLI module, using the '+loadvpi' option, and with the 'vpi_compat_bootstrap'
routine as the bootstrap routine. The Verilog code should contain the 
appropriate calls to the '$to_myhdl' and 'from_myhdl' tasks.

The 'myhdl_vpi.c' module was developed and verified with cver version
GPLCVER_1.10f on Linux.
