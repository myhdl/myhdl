from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import tempfile
import subprocess
import difflib
import warnings

from collections import namedtuple

import myhdl
from myhdl._Simulation import Simulation
from myhdl.conversion._toVHDL import toVHDL
from myhdl.conversion._toVerilog import toVerilog
from myhdl._block import _Block

_version = myhdl.__version__.replace('.', '')
# strip 'dev' for version
_version = _version.replace('dev', '')

_simulators = {}

sim = namedtuple('sim', 'name hdl analyze elaborate simulate skiplines skipchars ignore')


def registerSimulator(name=None, hdl=None, analyze=None, elaborate=None, simulate=None,
                      skiplines=None, skipchars=None, ignore=None):
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
    _simulators[name] = sim(name, hdl, analyze, elaborate, simulate, skiplines, skipchars, ignore)

registerSimulator(
    name="ghdl",
    hdl="VHDL",
    analyze="ghdl -a --std=08 --workdir=work pck_myhdl_%(version)s.vhd %(topname)s.vhd",
    elaborate="ghdl -e --std=08 --workdir=work %(unitname)s",
    simulate="ghdl -r --workdir=work %(unitname)s"
)

registerSimulator(
    name="nvc",
    hdl="VHDL",
    analyze="nvc --work=work_nvc -a pck_myhdl_%(version)s.vhd %(topname)s.vhd",
    elaborate="nvc --work=work_nvc -e %(topname)s",
    simulate="nvc --work=work_nvc -r %(topname)s"
)

registerSimulator(
    name="vlog",
    hdl="Verilog",
    analyze="vlog -work work_vlog %(topname)s.v",
    simulate='vsim work_vlog.%(topname)s -quiet -c -do "run -all; quit -f"',
    skiplines=6,
    skipchars=2,
    ignore=("# **", "# //", "# run -all")
)

registerSimulator(
    name="vcom",
    hdl="VHDL",
    analyze="vcom -2008 -work work_vcom pck_myhdl_%(version)s.vhd %(topname)s.vhd",
    simulate='vsim work_vcom.%(topname)s -quiet -c -do "run -all; quit -f"',
    skiplines=6,
    skipchars=2,
    ignore=("# **", "# //", "#    Time:", "# run -all")
)


registerSimulator(
    name="iverilog",
    hdl="Verilog",
    analyze="iverilog -o %(topname)s.o %(topname)s.v",
    simulate="vvp %(topname)s.o"
)

registerSimulator(
    name="cver",
    hdl="Verilog",
    analyze="cver -c -q %(topname)s.v",
    simulate="cver -q %(topname)s.v",
    skiplines=3
)


class _VerificationClass(object):

    __slots__ = ("simulator", "_analyzeOnly")

    def __init__(self, analyzeOnly=False):
        self.simulator = None
        self._analyzeOnly = analyzeOnly

    def __call__(self, func, *args, **kwargs):

        if not self.simulator:
            raise ValueError("No simulator specified")
        if self.simulator not in _simulators:
            raise ValueError("Simulator %s is not registered" % self.simulator)
        hdlsim = _simulators[self.simulator]
        hdl = hdlsim.hdl
        if hdl == 'Verilog' and toVerilog.name is not None:
            name = toVerilog.name
        elif hdl == 'VHDL' and toVHDL.name is not None:
            name = toVHDL.name
        elif isinstance(func, _Block):
            name = func.func.__name__
        else:
            warnings.warn(
                "\n    analyze()/verify(): Deprecated usage: See http://dev.myhdl.org/meps/mep-114.html", stacklevel=2)
            try:
                name = func.__name__
            except:
                raise TypeError(str(type(func)))

        vals = {}
        vals['topname'] = name
        vals['unitname'] = name.lower()
        vals['version'] = _version

        analyze = hdlsim.analyze % vals
        elaborate = hdlsim.elaborate
        if elaborate is not None:
            elaborate = elaborate % vals
        simulate = hdlsim.simulate % vals
        skiplines = hdlsim.skiplines
        skipchars = hdlsim.skipchars
        ignore = hdlsim.ignore

        if isinstance(func, _Block):
            if hdl == "VHDL":
                inst = func.convert(hdl='VHDL')
            else:
                inst = func.convert(hdl='Verilog')
        else:
            if hdl == "VHDL":
                inst = toVHDL(func, *args, **kwargs)
            else:
                inst = toVerilog(func, *args, **kwargs)

        if hdl == "VHDL":
            if not os.path.exists("work"):
                os.mkdir("work")
        if hdlsim.name in ('vlog', 'vcom'):
            if not os.path.exists("work_vsim"):
                try:
                    subprocess.call("vlib work_vlog", shell=True)
                    subprocess.call("vlib work_vcom", shell=True)
                    subprocess.call("vmap work_vlog work_vlog", shell=True)
                    subprocess.call("vmap work_vcom work_vcom", shell=True)
                except:
                    pass

        # print(analyze)
        ret = subprocess.call(analyze, shell=True)
        if ret != 0:
            print("Analysis failed", file=sys.stderr)
            return ret

        if self._analyzeOnly:
            print("Analysis succeeded", file=sys.stderr)
            return 0

        f = tempfile.TemporaryFile(mode='w+t')
        sys.stdout = f
        sim = Simulation(inst)
        sim.run()
        sys.stdout = sys.__stdout__
        f.flush()
        f.seek(0)

        flines = f.readlines()
        f.close()
        if not flines:
            print("No MyHDL simulation output - nothing to verify", file=sys.stderr)
            return 1

        if elaborate is not None:
            # print(elaborate)
            ret = subprocess.call(elaborate, shell=True)
            if ret != 0:
                print("Elaboration failed", file=sys.stderr)
                return ret

        g = tempfile.TemporaryFile(mode='w+t')
        # print(simulate)
        ret = subprocess.call(simulate, stdout=g, shell=True)
    #    if ret != 0:
    #        print "Simulation run failed"
    #        return
        g.flush()
        g.seek(0)

        glines = g.readlines()[skiplines:]
        if ignore:
            for p in ignore:
                glines = [line for line in glines if not line.startswith(p)]
        # limit diff window to the size of the MyHDL output
        # this is a hack to remove an eventual simulator postamble
        if len(glines) > len(flines):
            glines = glines[:len(flines)]
        glines = [line[skipchars:] for line in glines]
        flinesNorm = [line.lower() for line in flines]
        glinesNorm = [line.lower() for line in glines]
        g = difflib.unified_diff(flinesNorm, glinesNorm, fromfile='MyHDL', tofile=hdlsim.name)

        MyHDLLog = "MyHDL.log"
        HDLLog = hdlsim.name + ".log"
        try:
            os.remove(MyHDLLog)
            os.remove(HDLLog)
        except:
            pass

        s = "".join(g)
        f = open(MyHDLLog, 'w')
        g = open(HDLLog, 'w')
        d = open('diff.log', 'w')
        f.writelines(flines)
        g.writelines(glines)
        d.write(s)
        f.close()
        g.close()
        d.close()

        if not s:
            print("Conversion verification succeeded", file=sys.stderr)
        else:
            print("Conversion verification failed", file=sys.stderr)
            # print >> sys.stderr, s ,
            return 1

        return 0


verify = _VerificationClass(analyzeOnly=False)
analyze = _VerificationClass(analyzeOnly=True)
