#!/bin/bash

echo > pypystats.dat

tests="
timer
lfsr24
randgen
longdiv
findmax
"

for test in $tests
do
echo Test: $test >> pypystats.dat
echo ===== >> pypystats.dat


echo pypy >> pypystats.dat
echo ---- >> pypystats.dat
/usr/bin/time -o pypystats.dat -a -p pypy test_$test.py > ${test}_pypy.out
echo >> pypystats.dat


done



