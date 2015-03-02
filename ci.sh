#!/bin/bash

echo "Running $CI_TARGET tests"

if [ "$CI_TARGET" == "core" ]; then
  make -C myhdl/test/core
  py.test myhdl/test/core2
elif [ "$CI_TARGET" == "icarus" ]; then
  echo "======================================================================="
  echo "=========== A. Test Converted Verilog Code                    ========="
  echo "======================================================================="
  make -C "myhdl/test/conversion/general" icarus

  echo "======================================================================="
  echo "=========== B. Test Co-Simulation with Converted Verilog Code ========="
  echo "======================================================================="
  make -C cosimulation/icarus
  make -C myhdl/test/conversion/toVerilog
fi
