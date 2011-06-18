#!/bin/bash

echo > cvcstats.dat

python convert.py

tests="
timer
lfsr24
randgen
longdiv
findmax
"

for test in $tests
do

echo Test: $test >> cvcstats.dat
echo ===== >> cvcstats.dat

echo cvc compiled >> cvcstats.dat
echo ------------ >> cvcstats.dat
cvc -O +2state test_$test.v
/usr/bin/time -o cvcstats.dat -a -p ./cvcsim > ${test}_cvcexe.out
echo >> cvcstats.dat

echo cvc interpreted >> cvcstats.dat
echo --------------- >> cvcstats.dat
/usr/bin/time -o cvcstats.dat -a -p cvc +interp test_$test.v > ${test}_cvcinterp.out
echo >> cvcstats.dat

done



