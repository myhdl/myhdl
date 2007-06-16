import sys
import os
import tempfile
import subprocess
import difflib

import myhdl
from myhdl._Simulation import Simulation
from myhdl.conversion._toVHDL import toVHDL
from myhdl.conversion._toVerilog import toVerilog

_version = myhdl.__version__.replace('.','')
_simulators = []
_analyzeCommands = {}
_elaborateCommands = {}
_simulateCommands = {}

def registerSimulator(name=None, analyze=None, elaborate=None, simulate=None):
    if not isinstance(name, str) or (name.strip() == ""):
        raise ValueError("Invalid simulator name")
    if not isinstance(analyze, str) or (analyze.strip() == ""):
        raise ValueError("Invalid analyzer command")
    # elaborate command is optional
    if elaborate is not None:
        if not isinstance(elaborate, str) or (elaborate.strip() == ""):
            raise ValueError("Invalid elaborate command")
    if not isinstance(simulate, str) or (simulate.strip() == ""):
        raise ValueError("Invalid simulator command")
    _simulators.append(name)
    _analyzeCommands[name] = analyze
    _elaborateCommands[name] = elaborate
    _simulateCommands[name] = simulate

registerSimulator(name="GHDL",
                  analyze="ghdl -a --workdir=work pck_myhdl_%(version)s.vhd %(topname)s.vhd",
                  elaborate="ghdl -e --workdir=work %(topname)s",
                  simulate="ghdl -r %(topname)s")


class  _VerificationClass(object):

    __slots__ = ("simulator", "_analyzeOnly")

    def __init__(self, analyzeOnly=False):
        self.simulator = "GHDL"
        self._analyzeOnly = analyzeOnly


    def __call__(self, func, *args, **kwargs):

        vals = {}
        vals['topname'] = func.func_name
        vals['version'] = _version

        hdl = self.simulator
        if not hdl:
            raise ValueError("No simulator specified")
        if  not hdl in _simulators:
            raise ValueError("Simulator %s is not registered" % hdl)
        analyze = _analyzeCommands[hdl] % vals
        elaborate = _elaborateCommands[hdl]
        if elaborate is not None:
            elaborate = elaborate % vals
        simulate = _simulateCommands[hdl] % vals
        
        inst = toVHDL(func, *args, **kwargs)
        
        if not os.path.exists("work"):
            os.mkdir("work")
        ret = subprocess.call(analyze, shell=True)
        if ret != 0:
            print >> sys.stderr, "Analysis failed"
            return ret

        if self._analyzeOnly:
            print >> sys.stderr, "Analysis succeeded"
            return 0

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
            print >> sys.stderr, "No MyHDL simulation output - nothing to verify"
            return 1


        if elaborate is not None:
            ret = subprocess.call(elaborate, shell=True)
            if ret != 0:
                print >> sys.stderr, "Elaboration failed"
                return ret
            
        g = tempfile.TemporaryFile()
        ret = subprocess.call(simulate, stdout=g, shell=True)
    #    if ret != 0:
    #        print "Simulation run failed"
    #        return
        g.flush()
        g.seek(0)

        glines = g.readlines()
        flinesNorm = [line.lower() for line in flines]
        glinesNorm = [line.lower() for line in glines]
        g = difflib.unified_diff(flinesNorm, glinesNorm, fromfile=hdl, tofile="VHDL")

        MyHDLLog = "MyHDL.log"
        HDLLog = hdl + ".log"
        try:
            os.remove(MyHDLLog)
            os.remove(HDLLog)
        except:
            pass


        s = "".join(g)
        f = open(MyHDLLog, 'w')
        g = open(HDLLog, 'w')
        f.writelines(flines)
        g.writelines(glines)


        if not s:
            print >> sys.stderr, "Conversion verification succeeded"
        else:
            print >> sys.stderr, "Conversion verification failed"
            # print >> sys.stderr, s ,
            return 1

        return 0


verify = _VerificationClass(analyzeOnly=False)
analyze = _VerificationClass(analyzeOnly=True)
