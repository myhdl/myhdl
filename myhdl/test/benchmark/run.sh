#!/bin/bash

echo > stats.dat

python convert.py

ghdl -a pck_myhdl_07.vhd

tests="
lfsr24
longdiv
randgen
"

for test in $tests
do
echo Test: $test >> stats.dat
echo ===== >> stats.dat

echo python >> stats.dat
echo ------ >> stats.dat
#/usr/bin/time -o stats.dat -a -p python test_$test.py > $test_python.out
echo >> stats.dat

echo pypy >> stats.dat
echo ---- >> stats.dat
/usr/bin/time -o stats.dat -a -p pypy test_$test.py > $test_pypy.out
echo >> stats.dat

echo icarus >> stats.dat
echo ------ >> stats.dat
iverilog test_$test.v
/usr/bin/time -o stats.dat -a -p vvp a.out test_$test > $test_icarus.out
echo >> stats.dat

echo ghdl >> stats.dat
echo ---- >> stats.dat
ghdl -a test_$test.vhd 
ghdl -e test_$test
/usr/bin/time -o stats.dat -a -p ghdl -r test_$test > $test_ghdl.out
echo >> stats.dat

echo vlog >> stats.dat
echo ---- >> stats.dat
vlog test_$test.v 
/usr/bin/time -o stats.dat -a -p vsim -c -do run.do test_$test > $test_vlog.out
echo >> stats.dat

echo vcom >> stats.dat
echo ---- >> stats.dat
vcom test_$test.vhd 
/usr/bin/time -o stats.dat -a -p vsim -c -do run.do test_$test > $test_vcom.out
echo >> stats.dat

done



