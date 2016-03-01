#!/bin/bash
set -evx
wget https://sourceforge.net/projects/ghdl-updates/files/Builds/ghdl-0.33/debian/ghdl_0.33-1ubuntu1_amd64.deb -O /tmp/ghdl.tar.gz
mkdir ghdl-0.33
tar -C ghdl-0.33 -xvf /tmp/ghdl.tar.gz
