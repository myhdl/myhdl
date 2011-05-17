#!/bin/bash

echo > stats.out

ghdl -a pck_myhdl_07.vhd

self_tests="
divider
"

for test in $self_tests
do
echo Test: $test >> stats.out
echo ===== >> stats.out


echo pypy >> stats.out
echo ---- >> stats.out
/usr/bin/time -o stats.out -a -p pypy test_$test.py
echo >> stat.out

echo icarus >> stats.out
echo ------ >> stats.out
iverilog test_$test.v
/usr/bin/time -o stats.out -a -p vvp a.out test_$test
echo >> stat.out

echo ghdl >> stats.out
echo ---- >> stats.out
ghdl -a test_$test.vhd 
ghdl -e test_$test
/usr/bin/time -o stats.out -a -p ghdl -r test_$test
echo >> stats.out

echo vlog >> stats.out
echo ---- >> stats.out
vlog test_$test.v 
/usr/bin/time -o stats.out -a -p vsim -c -do run.do test_$test
echo >> stats.out

echo vcom >> stats.out
echo ---- >> stats.out
vcom test_$test.vhd 
/usr/bin/time -o stats.out -a -p vsim -c -do run.do test_$test
echo >> stats.out

done

