#!/bin/bash

echo > teststats.dat

python convert.py

ghdl -a pck_myhdl_08dev.vhd
vlib work
vcom pck_myhdl_08dev.vhd

tests="
findmax
"

for test in $tests
do
echo Test: $test >> teststats.dat
echo ===== >> teststats.dat

echo python >> teststats.dat
echo ------ >> teststats.dat
#/usr/bin/time -o teststats.dat -a -p python test_$test.py > ${test}_python.out
echo >> teststats.dat

echo pypy >> teststats.dat
echo ---- >> teststats.dat
/usr/bin/time -o teststats.dat -a -p pypy test_$test.py > ${test}_pypy.out
echo >> teststats.dat

echo icarus >> teststats.dat
echo ------ >> teststats.dat
iverilog test_$test.v
/usr/bin/time -o teststats.dat -a -p vvp a.out test_$test > ${test}_icarus.out
echo >> teststats.dat

echo ghdl >> teststats.dat
echo ---- >> teststats.dat
ghdl -a test_$test.vhd 
ghdl -e test_$test
#/usr/bin/time -o teststats.dat -a -p ghdl -r test_$test > ${test}_ghdl.out
echo >> teststats.dat

echo vlog >> teststats.dat
echo ---- >> teststats.dat
vlog test_$test.v 
/usr/bin/time -o teststats.dat -a -p vsim -c -do run.do test_$test > ${test}_vlog.out
echo >> teststats.dat

echo vcom >> teststats.dat
echo ---- >> teststats.dat
vcom test_$test.vhd 
/usr/bin/time -o teststats.dat -a -p vsim -c -do run.do test_$test > ${test}_vcom.out
echo >> teststats.dat

done



