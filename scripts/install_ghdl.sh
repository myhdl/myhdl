#!/bin/bash
set -evx
wget https://sourceforge.net/projects/ghdl-updates/files/Builds/ghdl-0.33/ghdl-0.33-x86_64-linux.tgz -O /tmp/ghdl.tar.gz
mkdir ghdl-0.33
tar -C ghdl-0.33 -xvf /tmp/ghdl.tar.gz
