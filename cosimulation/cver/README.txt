A working cver installation is required.

Use the makefile corresponding to your platform to generate a 'myhdl.so'
PLI module. Currently, the following makefiles are available:

  makefile.lnx  - for Linux

To test whether it works, go to the 'test' subdirectory and run the
tests with 'python test_all.py'. 

For co-simulation with MyHDL, 'cver' should be run with the 'myhdl.so'
PLI module, using the '+loadvpi' option, and with the 'vpi_compat_bootstrap'
routine as the bootstrap routine. The Verilog code should contain the 
appropriate calls to the '$to_myhdl' and 'from_myhdl' tasks.

The 'myhdl.c' module was developed and verified with cver version
GPLCVER_1.10f on Linux.
