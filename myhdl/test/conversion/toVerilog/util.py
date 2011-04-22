import os
path = os.path

from myhdl import *

# Icarus
def setupCosimulationIcarus(**kwargs):
    name = kwargs['name']
    objfile = "%s.o" % name
    if path.exists(objfile):
        os.remove(objfile)
    analyze_cmd = "iverilog -o %s %s.v tb_%s.v" % (objfile, name, name)
    os.system(analyze_cmd)
    simulate_cmd = "vvp -m ../../../../cosimulation/icarus/myhdl.vpi %s" % objfile
    return Cosimulation(simulate_cmd, **kwargs)

# cver
def setupCosimulationCver(**kwargs):
    name = kwargs['name']
    cmd = "cver -q +loadvpi=../../../../cosimulation/cver/myhdl_vpi:vpi_compat_bootstrap " + \
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
#setupCosimulation = setupCosimulationCver

verilogCompile = verilogCompileIcarus
#verilogCompile = verilogCompileCver
