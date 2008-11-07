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
_hdlMap = {}
_analyzeCommands = {}
_elaborateCommands = {}
_simulateCommands = {}
_offsets = {}

def registerSimulator(name=None, hdl=None, analyze=None, elaborate=None, simulate=None, offset=0):
    if not isinstance(name, str) or (name.strip() == ""):
        raise ValueError("Invalid simulator name")
    if hdl not in ("VHDL", "Verilog"):
        raise ValueError("Invalid hdl %s" % hdl)
    if not isinstance(analyze, str) or (analyze.strip() == ""):
        raise ValueError("Invalid analyzer command")
    # elaborate command is optional
    if elaborate is not None:
        if not isinstance(elaborate, str) or (elaborate.strip() == ""):
            raise ValueError("Invalid elaborate command")
    if not isinstance(simulate, str) or (simulate.strip() == ""):
        raise ValueError("Invalid simulator command")
    _simulators.append(name)
    _hdlMap[name] = hdl
    _analyzeCommands[name] = analyze
    _elaborateCommands[name] = elaborate
    _simulateCommands[name] = simulate
    _offsets[name] = offset

registerSimulator(
    name="GHDL",
    hdl="VHDL",
    analyze="ghdl -a --workdir=work pck_myhdl_%(version)s.vhd %(topname)s.vhd",
    elaborate="ghdl -e --workdir=work -o %(unitname)s_ghdl %(topname)s",
    simulate="ghdl -r %(unitname)s_ghdl"
    )

registerSimulator(
    name="icarus",
    hdl="Verilog",
    analyze="iverilog -o %(topname)s.o %(topname)s.v",
    simulate="vvp %(topname)s.o"
    )

registerSimulator(
    name="cver",
    hdl="Verilog",
    analyze="cver -c -q %(topname)s.v",
    simulate="cver -q %(topname)s.v",
    offset=3
    )


class  _VerificationClass(object):

    __slots__ = ("simulator", "_analyzeOnly")

    def __init__(self, analyzeOnly=False):
        self.simulator = "GHDL"
        self._analyzeOnly = analyzeOnly


    def __call__(self, func, *args, **kwargs):

        vals = {}
        vals['topname'] = func.func_name
        vals['unitname'] = func.func_name.lower()
        vals['version'] = _version

        hdlsim = self.simulator
        if not hdlsim:
            raise ValueError("No simulator specified")
        if  not hdlsim in _simulators:
            raise ValueError("Simulator %s is not registered" % hdlsim)
        hdl  = _hdlMap[hdlsim]
        analyze = _analyzeCommands[hdlsim] % vals
        elaborate = _elaborateCommands[hdlsim]
        if elaborate is not None:
            elaborate = elaborate % vals
        simulate = _simulateCommands[hdlsim] % vals
        offset = _offsets[hdlsim]

        if hdl == "VHDL":
            inst = toVHDL(func, *args, **kwargs)
        else:
            inst = toVerilog(func, *args, **kwargs)

        if hdl == "VHDL":
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

        glines = g.readlines()[offset:]
        flinesNorm = [line.lower() for line in flines]
        glinesNorm = [line.lower() for line in glines]
        g = difflib.unified_diff(flinesNorm, glinesNorm, fromfile=hdlsim, tofile=hdl)

        MyHDLLog = "MyHDL.log"
        HDLLog = hdlsim + ".log"
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
