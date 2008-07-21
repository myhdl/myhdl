Original tests for conversion to Verilog
----------------------------------------

Requirements:
  * cver or icarus 
  * co-simulation with the target simulator enabled  

cver is setup by default. You can change that by going into util.py
and using the Icarus definitions for the functions setupCosimulation
and verilogCompile.

The test suite should run without errors or failures with Cver
(GPLCVER_2.11a). However, with Icarus 0.8.1 some tests in test_dec and
test_signed fail. It has been found that Icarus 0.8 is currently
unreliable for signed arithmetic. It has been reported that the issues
are addressed in 0.9 development.
