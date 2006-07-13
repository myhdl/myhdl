import sys
import tempfile
import subprocess
import difflib

from myhdl import *

def verifyConversion(func, *args, **kwargs):
    inst = toVHDL(func, *args, **kwargs)

    f = tempfile.TemporaryFile()
    sys.stdout = f
    sim = Simulation(inst)
    sim.run()
    sys.stdout = sys.__stdout__
    f.flush()
    f.seek(0)

    topname = func.func_name
    ret = subprocess.call(["ghdl", "-a", "--workdir=work", "%s.vhd" % topname])
    if ret != 0:
        print "Analysis failed"
        return
    ret = subprocess.call(["ghdl", "-e", "--workdir=work", topname])
    if ret != 0:
        print "Elaboration failed"
        return
    g = tempfile.TemporaryFile()
    ret = subprocess.call(["ghdl", "-r", topname], stdout=g)
    if ret != 0:
        print "Simulation run failed"
        return
    g.flush()
    g.seek(0)


    g = difflib.unified_diff(f.readlines(), g.readlines(), fromfile="MyHDL", tofile="VHDL")


    s = "".join(g)
    if not s:
        print "Conversion verification succeeded"
    else:
        print "Conversion verification failed"
        print s ,
