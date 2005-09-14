import os
path = os.path

from myhdl import *

def setupCosimulation(**kwargs):
    name = kwargs['name']
    objfile = "%s.o" % name
    if path.exists(objfile):
        os.remove(objfile)
    analyze_cmd = "iverilog -o %s %s.v tb_%s.v" % (objfile, name, name)
    os.system(analyze_cmd)
    simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile
    return Cosimulation(simulate_cmd, **kwargs)
    
