import os, sys
path = os.path
import subprocess
from glob import glob
from myhdl import Cosimulation


_this = path.dirname(path.abspath(__file__))
_cosim = path.normpath(f"{_this}/../../../../cosimulation")


# Icarus
def setupCosimulationIcarus(**kwargs):
    name = kwargs['name']
    objfile = "%s.o" % name
    if path.exists(objfile):
        os.remove(objfile)
    analyze_cmd = ['iverilog', '-o', objfile, '%s.v' % name, 'tb_%s.v' % name]
    subprocess.call(analyze_cmd)
    vpifile = "myhdl"
    vpifiles = glob("**/myhdl.vpi", recursive=True)
    if 1 == len(vpifiles):
        vpifile = vpifiles[0]
    elif sys.platform != "win32":
        vpifile = f"{_cosim}/icarus/myhdl.vpi"
    simulate_cmd = ['vvp', '-m', vpifile, objfile]
    return Cosimulation(simulate_cmd, **kwargs)


# cver
def setupCosimulationCver(**kwargs):
    name = kwargs['name']
    cmd = f"cver -q +loadvpi={_cosim}/cver/myhdl_vpi:vpi_compat_bootstrap " + \
          "%s.v tb_%s.v " % (name, name)
    return Cosimulation(cmd, **kwargs)


def verilogCompileIcarus(name):
    objfile = "%s.o" % name
    if path.exists(objfile):
        os.remove(objfile)
    analyze_cmd = "iverilog -o %s %s.v tb_%s.v" % (objfile, name, name)
    os.system(analyze_cmd)


def verilogCompileCver(name):
    cmd = "cver -c %s.v" % name
    os.system(cmd)


setupCosimulation = setupCosimulationIcarus
# setupCosimulation = setupCosimulationCver

verilogCompile = verilogCompileIcarus
# verilogCompile = verilogCompileCver
