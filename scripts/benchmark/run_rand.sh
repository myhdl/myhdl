echo > stats.out

ghdl -a pck_myhdl_07.vhd
vcom  pck_myhdl_07.vhd


echo >> stat.out
echo random_generator >> stats.out
echo ======= >> stats.out


echo pypy >> stats.out
echo ---- >> stats.out
/usr/bin/time -o stats.out -a -p pypy test_random_generator.py > random_pypy.out
echo >> stat.out

echo icarus >> stats.out
echo ------ >> stats.out
iverilog test_random_generator.v
/usr/bin/time -o stats.out -a -p vvp a.out test_random_generator > random_vvp.out
echo >> stat.out

echo ghdl >> stats.out
echo ---- >> stats.out
ghdl -a test_random_generator.vhd 
ghdl -e test_random_generator
/usr/bin/time -o stats.out -a -p ghdl -r test_random_generator > random_ghdl.out
echo >> stat.out

echo vlog >> stats.out
echo ---- >> stats.out
vlog test_random_generator.v 
/usr/bin/time -o stats.out -a -p vsim -c -do run.do test_random_generator > random_vlog.out
echo >> stat.out

echo vcom >> stats.out
echo ---- >> stats.out
vcom test_random_generator.vhd
/usr/bin/time -o stats.out -a -p vsim -c -do run.do test_random_generator > random_vcom.out
echo >> stat.out

