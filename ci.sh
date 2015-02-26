#!/bin/bash

echo "Running $CI_TARGET tests"

if [ "$CI_TARGET" == "core" ]; then
  make -C myhdl/test/core
elif [ "$CI_TARGET" == "icarus" ]; then
  sudo apt-get update -qq
  sudo apt-get install -y iverilog
  make -C "myhdl/test/conversion/general" icarus
fi
