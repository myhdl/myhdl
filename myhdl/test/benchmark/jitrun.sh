#!/bin/bash

echo > jitstats.dat

tests="
longdiv_9
longdiv_10
longdiv_11
longdiv_12
longdiv_13
longdiv_14
longdiv_15
longdiv_16
longdiv_17
longdiv_18
"

for test in $tests
do
echo Test: $test >> jitstats.dat
echo ===== >> jitstats.dat

echo python >> jitstats.dat
echo ------ >> jitstats.dat
/usr/bin/time -o jitstats.dat -a -p python test_$test.py > ${test}_python.out
echo >> jitstats.dat

echo pypy >> jitstats.dat
echo ---- >> jitstats.dat
/usr/bin/time -o jitstats.dat -a -p pypy test_$test.py > ${test}_pypy.out
echo >> jitstats.dat

done



