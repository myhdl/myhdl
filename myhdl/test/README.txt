Welcome to the MyHDL test directory tree.

This directory contains a number of subdirectories, that contain tests
for various aspects of MyHDL.

  * core - the MyHDL modeling core tests
  * conversion - tests related to conversion from MyHDL to Verilog/VHDL
  * bugs - tests for specific bugs that were reported and solved

All test directories contain a Makefile for easy testing. However,
there may be additional dependencies and requirements. Some tests
require a working installation for the Verilog simulators cver or
Icarus, or the VHDL simulator GHDL. In addition, some tests require a
that co-simulation is properly set up.

Moreover, some test dirs use the py.test unit testing framework
instead of the standard Python unittest library.

Please consult the README.txt file in each subdirectory for
instructions.

Note however that the core tests can be run with stock Python and
stock MyHDL without any additional requirements. Whenever you make a
code change, these are the first tests that you want to run to make
sure nothing is broken.
