#!/bin/bash


# {{{ Utilities
# {{{ cfont
cfont() {
while (($#!=0))
do
  case $1 in
    -b)           echo -ne " " ;;
    -t)           echo -ne "\t";;
    -n)           echo -ne "\n";;
    -black)       echo -ne "\033[30m";;
    -red)         echo -ne "\033[31m";;
    -green)       echo -ne "\033[32m";;
    -yellow)      echo -ne "\033[33m";;
    -blue)        echo -ne "\033[34m";;
    -purple)      echo -ne "\033[35m";;
    -cyan)        echo -ne "\033[36m";;
    -white|-gray) echo -ne "\033[37m";;
    -reset)       echo -ne "\033[0m";;
    -h|-help|--help)
      echo "Usage: cfont -color1 message1 -color2 message2 ...";
      echo "eg:       cfont -red [ -blue message1 message2 -red ]";
      ;;
    *)
      echo -ne "$1"
      ;;
  esac
  shift
done
}
# }}}

# {{{ print_heading
print_heading() {
  msg="$@"

  line=$(printf '%0.1s' "="{1..80})

  lPad=$(( ( 80 - ${#msg} ) / 2 - 1 ))
  [[ $lPad -lt 0 ]] && lPad=0
  pad="${line::$lPad}"

  cfont -cyan
  echo $line
  echo $pad $msg $pad
  echo $line
  cfont -reset
}
# }}}

# {{{ run_test
run_test() {
  cfont -cyan; echo "running test: $command $@" ; cfont -n -reset
  $command "$@"

  if [ $? -ne 0 ]; then
    cfont -red; echo "test failed: $command $@" ; cfont -n -reset
    foundError=1
  else
    cfont -green "OK" -n -reset
  fi
}
# }}}

# }}}

foundError=0
echo "Running $CI_TARGET tests"

CI_TARGET=${CI_TARGET:-core}
if [ "$CI_TARGET" == "core" ]; then

  print_heading "Core MyHDL Testbench"
  run_test make -C myhdl/test/core
  run_test make -C myhdl/test/core2

elif [ "$CI_TARGET" == "icarus" ]; then

  print_heading "Test Converted Verilog Code"
  run_test make -C "myhdl/test/conversion/general" icarus

  print_heading "Test Co-Simulation with Converted Verilog Code" 
  run_test make -C cosimulation/icarus
  run_test make -C myhdl/test/conversion/toVerilog

elif [ "$CI_TARGET" == "ghdl" ]; then

  print_heading "Test Converted VHDL Code"
  run_test make -C "myhdl/test/conversion/general" GHDL

  print_heading "Test Co-Simulation with Converted VHDL Code" 
  run_test make -C myhdl/test/conversion/toVHDL GHDL
fi

exit $foundError

