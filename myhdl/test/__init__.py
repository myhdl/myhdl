import sys
import os
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

    flines = f.readlines()
    f.close()
    if not flines:
        print "No MyHDL simulation output - nothing to verify"
        return

    if not os.path.exists("work"):
        os.mkdir("work")

    topname = func.func_name
    ret = subprocess.call(["ghdl", "-a", "--workdir=work", "%s.vhd" % topname])
    if ret != 0:
        print "Analysis failed"
        return ret
    ret = subprocess.call(["ghdl", "-e", "--workdir=work", topname])
    if ret != 0:
        print "Elaboration failed"
        return ret
    g = tempfile.TemporaryFile()
    ret = subprocess.call(["ghdl", "-r", topname], stdout=g)
#    if ret != 0:
#        print "Simulation run failed"
#        return
    g.flush()
    g.seek(0)


    glines = g.readlines()
    flinesNorm = [line.lower() for line in flines]
    glinesNorm = [line.lower() for line in glines]
    g = difflib.unified_diff(flinesNorm, glinesNorm, fromfile="MyHDL", tofile="VHDL")

    MyHDLLog = "MyHDL.log"
    GHDLLog = "GHDL.log"
    try:
        os.remove(MyHDLLog)
        os.remove(GHDLLog)
    except:
        pass


    s = "".join(g)
    f = open(MyHDLLog, 'w')
    g = open(GHDLLog, 'w')
    f.writelines(flinesNorm)
    g.writelines(glinesNorm)

    
    if not s:
        print "Conversion verification succeeded"
    else:
        print "Conversion verification failed"
        print s ,
        return 1

    return 0
