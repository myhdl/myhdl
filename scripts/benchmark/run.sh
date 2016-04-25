#!/bin/bash

echo > stats.dat

pypy convert.py

ghdl -a --std=08 pck_myhdl_10.vhd
# vlib work
# vcom pck_myhdl_08dev.vhd

tests="
timer
lfsr24
randgen
longdiv
findmax
"

for test in $tests
do
echo Test: $test >> stats.dat
echo ===== >> stats.dat

echo python >> stats.dat
echo ------ >> stats.dat
/usr/bin/time -o stats.dat -a -p python test_$test.py > ${test}_python.out
echo >> stats.dat

echo pypy >> stats.dat
echo ---- >> stats.dat
/usr/bin/time -o stats.dat -a -p pypy test_$test.py > ${test}_pypy.out
echo >> stats.dat

echo icarus >> stats.dat
echo ------ >> stats.dat
iverilog test_$test.v
/usr/bin/time -o stats.dat -a -p vvp a.out test_$test > ${test}_icarus.out
echo >> stats.dat

echo ghdl >> stats.dat
echo ---- >> stats.dat
ghdl -a --std=08 test_$test.vhd
ghdl -e --std=08 test_$test
/usr/bin/time -o stats.dat -a -p ghdl -r test_$test > ${test}_ghdl.out
echo >> stats.dat

# echo vlog >> stats.dat
# echo ---- >> stats.dat
# vlog test_$test.v
# /usr/bin/time -o stats.dat -a -p vsim -c -do run.do test_$test > ${test}_vlog.out
# echo >> stats.dat
#
# echo vcom >> stats.dat
# echo ---- >> stats.dat
# vcom test_$test.vhd
# /usr/bin/time -o stats.dat -a -p vsim -c -do run.do test_$test > ${test}_vcom.out
# echo >> stats.dat

done
