#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" myhdl _extractHierarchy module.

"""
from __future__ import absolute_import
from __future__ import print_function

import sys
import inspect
from inspect import currentframe, getframeinfo, getouterframes
import re
import string
from types import GeneratorType
import linecache

from myhdl import ExtractHierarchyError, ToVerilogError, ToVHDLError
from myhdl._Signal import _Signal, _isListOfSigs
from myhdl._util import _isGenFunc, _flatten, _genfunc
from myhdl._misc import _isGenSeq
from myhdl._resolverefs import _resolveRefs
from myhdl._getcellvars import _getCellVars


_profileFunc = None

class _error:
    pass
_error.NoInstances = "No instances found"
_error.InconsistentHierarchy = "Inconsistent hierarchy - are all instances returned ?"
_error.InconsistentToplevel = "Inconsistent top level %s for %s - should be 1"


class _Instance(object):
    __slots__ = ['level', 'obj', 'subs', 'sigdict', 'memdict', 'name', 'func', 'argdict', 'objdict']
    def __init__(self, level, obj, subs, sigdict, memdict, func, argdict, objdict=None):
        self.level = level
        self.obj = obj
        self.subs = subs
        self.sigdict = sigdict
        self.memdict = memdict
        self.func = func
        self.argdict = argdict
        if objdict:
            self.objdict = objdict


_memInfoMap = {}

class _MemInfo(object):
    __slots__ = ['mem', 'name', 'elObj', 'depth', '_used', '_driven', '_read']
    def __init__(self, mem):
        self.mem = mem
        self.name = None
        self.depth = len(mem)
        self.elObj = mem[0]
        self._used = False
        self._driven = None
        self._read = None


def _getMemInfo(mem):
    return _memInfoMap[id(mem)]

def _makeMemInfo(mem):
    key = id(mem)
    if key not in _memInfoMap:
        _memInfoMap[key] = _MemInfo(mem)
    return _memInfoMap[key]

def _isMem(mem):
    return id(mem) in _memInfoMap

_userCodeMap = {'verilog' : {},
                'vhdl' : {}
               }

class _UserCode(object):
    __slots__ = ['code', 'namespace', 'funcname', 'func', 'sourcefile', 'sourceline']
    def __init__(self, code, namespace, funcname, func, sourcefile, sourceline):
        self.code = code
        self.namespace = namespace
        self.sourcefile = sourcefile
        self.func = func
        self.funcname = funcname
        self.sourceline = sourceline

    def __str__(self):
        try:
            code =  self._interpolate()
        except:
            type, value, tb = sys.exc_info()
            info = "in file %s, function %s starting on line %s:\n    " % \
                   (self.sourcefile, self.funcname, self.sourceline)
            msg = "%s: %s" % (type, value)
            self.raiseError(msg, info)
        code = "\n%s\n" % code
        return code

    def _interpolate(self):
        return string.Template(self.code).substitute(self.namespace)

class _UserCodeDepr(_UserCode):
    def _interpolate(self):
        return self.code % self.namespace

class _UserVerilogCode(_UserCode):
    def raiseError(self, msg, info):
        raise ToVerilogError("Error in user defined Verilog code", msg, info)

class _UserVhdlCode(_UserCode):
    def raiseError(self, msg, info):
        raise ToVHDLError("Error in user defined VHDL code", msg, info)

class _UserVerilogCodeDepr(_UserVerilogCode, _UserCodeDepr):
    pass

class _UserVhdlCodeDepr(_UserVhdlCode, _UserCodeDepr):
    pass


class _UserVerilogInstance(_UserVerilogCode):
    def __str__(self):
        args = inspect.getargspec(self.func)[0]
        s = "%s %s(" % (self.funcname, self.code)
        sep = ''
        for arg in args:
            if arg in self.namespace and isinstance(self.namespace[arg], _Signal):
                signame = self.namespace[arg]._name
                s += sep
                sep = ','
                s += "\n    .%s(%s)" % (arg, signame)
        s += "\n);\n\n"
        return s

class _UserVhdlInstance(_UserVhdlCode):
    def __str__(self):
        args = inspect.getargspec(self.func)[0]
        s = "%s: entity work.%s(MyHDL)\n" % (self.code, self.funcname)
        s += "    port map ("
        sep = ''
        for arg in args:
            if arg in self.namespace and isinstance(self.namespace[arg], _Signal):
                signame = self.namespace[arg]._name
                s += sep
                sep = ','
                s += "\n        %s=>%s" % (arg, signame)
        s += "\n    );\n\n"
        return s



def _addUserCode(specs, arg, funcname, func, frame):
    classMap = {
                '__verilog__' : _UserVerilogCodeDepr,
                '__vhdl__' :_UserVhdlCodeDepr,
                'verilog_code' : _UserVerilogCode,
                'vhdl_code' :_UserVhdlCode,
                'verilog_instance' : _UserVerilogInstance,
                'vhdl_instance' :_UserVhdlInstance,

               }
    namespace = frame.f_globals.copy()
    namespace.update(frame.f_locals)
    sourcefile = inspect.getsourcefile(frame)
    sourceline = inspect.getsourcelines(frame)[1]
    for hdl in _userCodeMap:
        oldspec = "__%s__" % hdl
        codespec = "%s_code" % hdl
        instancespec = "%s_instance" % hdl
        spec = None
        # XXX add warning logic
        if instancespec in specs:
            spec = instancespec
        elif codespec in specs:
            spec = codespec
        elif oldspec in specs:
            spec = oldspec
        if spec:
            assert id(arg) not in _userCodeMap[hdl]
            code = specs[spec]
            _userCodeMap[hdl][id(arg)] = classMap[spec](code, namespace, funcname, func, sourcefile, sourceline)


class _CallFuncVisitor(object):

    def __init__(self):
        self.linemap = {}

    def visitAssign(self, node):
        if isinstance(node.expr, ast.CallFunc):
            self.lineno = None
            self.visit(node.expr)
            self.linemap[self.lineno] = node.lineno

    def visitName(self, node):
        self.lineno = node.lineno


def dump_hierarchy(top_level, *args, **kwargs):
    """ debug utility that dumps a modules hierarchy """
    assert hasattr(top_level, '__call__')
    # make sure the function has no Python compile errors
    try:
        g = top_level(*args, **kwargs)
    except Exception as err:
        raise err

    print("\nHierarchy for \"{}\"  ".format(top_level.__name__)) 
    try:
        h = _HierExtr(top_level.__name__, top_level, *args, **kwargs)
        h.extract()
    except ExtractHierarchyError as err:
        print(str(err))        
    h._dump(h.hierarchy)
    print("")


class _HierExtr(object):

    def __init__(self, name, dut, *args, **kwargs):

        global _profileFunc
        _memInfoMap.clear()
        for hdl in _userCodeMap:
            _userCodeMap[hdl].clear()
        self.skipNames = ('always_comb', 'instance', \
                          'always_seq', '_always_seq_decorator', \
                          'always', '_always_decorator', \
                          'instances', \
                          'processes', 'posedge', 'negedge')
        self.skip = 0
        self.hierarchy = []
        self.absnames = {}
        self.level = 0
        self.name = name
        self.dut = dut
        self.args = args
        self.kwargs = kwargs

    def _get_name(self, obj):
        if hasattr(obj, '__name__'):
            name = obj.__name__
        elif hasattr(obj, 'func'):
            name = obj.func.__name__
        elif hasattr(obj, 'genfunc'):
            name = obj.genfunc.__name__
        elif isinstance(obj, (list, tuple)):
            name = '<gen list?>'
        else:
            name = 'unknown'
        return name

    def extract(self):
        """ extract the hierarchy """
        name = self.name
        hierarchy = self.hierarchy
        absnames = self.absnames
        _profileFunc = self.extractor
        sys.setprofile(_profileFunc)
        _top = self.dut(*self.args, **self.kwargs)
        sys.setprofile(None)
        if not hierarchy:
            raise ExtractHierarchyError(_error.NoInstances)

        self.top = _top

        # streamline hierarchy
        hierarchy.reverse()
        # walk the hierarchy to define relative and absolute names
        names = {}
        top_inst = hierarchy[0]
        obj, subs = top_inst.obj, top_inst.subs
        names[id(obj)] = name
        absnames[id(obj)] = name
        if not top_inst.level == 1:
            raise ExtractHierarchyError(_error.InconsistentToplevel % (top_inst.level, name))

        # verify the hierarchy is consistent and valid
        for inst in hierarchy:
            obj, subs = inst.obj, inst.subs
            if id(obj) not in names:
                name = self._get_name(obj)
                print("Hierarchy Error: {} {} ({}) missing ".format(name, type(obj), id(obj)))
                raise ExtractHierarchyError(_error.InconsistentHierarchy)
            inst.name = names[id(obj)]
            tn = absnames[id(obj)]
            for sn, so in subs:
                names[id(so)] = sn
                absnames[id(so)] = "%s_%s" % (tn, sn)
                if isinstance(so, (tuple, list)):
                    for i, soi in enumerate(so):
                        sni =  "%s_%s" % (sn, i)
                        names[id(soi)] = sni
                        absnames[id(soi)] = "%s_%s_%s" % (tn, sn, i)

    def _dump(self, hierarchy, obj=None, level=0, levels=-1):
        """ print out the hierarchy levels 
        The sys.profiler uses the self.extractor to examine the functions
        used in the design to be simulated / converted.  The self.extractor
        will create the `hierarchy` list.  The `hierarchy` is a list of 
        `_Instance`.  The `_Instance` contains information about the instance,
        this funciton will walk the list and print out the hierarchy.
        """                
        id_limit = 1000   # only use the 3 least sig digits
        tobj = obj        # object to highlight
        for ii, inst in enumerate(hierarchy): 
            if isinstance(inst, _Instance):
                gens = None
                if levels > 0 and inst.level > levels:
                    continue
                obj, subs = inst.obj, inst.subs
                indent = '  '*inst.level
                func, sid = inst.func, id(obj)%id_limit
                name = self._get_name(func)
                if level == 0 and name == 'unknown':
                    name = self.dut.__name__

                # the _Instance.obj should be a function or list of generators, 
                # the list of generators should have an associated function
                if isinstance(obj, (list, tuple)):
                    fc = ' ' if name == 'unknown' else ':'
                    lstr = ', '.join(["{:3d}".format(id(oo)%1000) for oo in obj])
                    print("{} {}{}({}) [{}]".format(indent, fc, name, sid, lstr), end='')
                    gens = obj
                else:
                    c = '*' if id(obj) == id(tobj) else ' '
                    print("{} +{}({})".format(indent, name, sid), end='')
                    # print the number of returns, number of signals, number of memories 
                    fstr = "{} has {}, {}, {}"
                    print(fstr.format(c, len(inst.argdict), 
                                      len(inst.sigdict), len(inst.memdict)), end='')
                    if len(subs) > 0:
                        gens = [gg[1] for gg in subs]

                if gens is not None:
                    rg = ", ".join(["{}".format(self._get_name(gg)) for gg in gens])
                    print("\n{}     returns {}".format(indent, rg))
                else:
                    print(" ")
            else:
                print("Error in hierarchy processing")

    def extractor(self, frame, event, arg):
        if event == "call":

            funcname = frame.f_code.co_name
            # skip certain functions
            if funcname in self.skipNames:
                self.skip +=1
            if not self.skip:
                self.level += 1

        elif event == "return":

            funcname = frame.f_code.co_name
            func = frame.f_globals.get(funcname)
            if func is None:
                # Didn't find a func in the global space, try the local "self"
                # argument and see if it has a method called *funcname*
                obj = frame.f_locals.get('self')
                if hasattr(obj, funcname):
                    func = getattr(obj, funcname)

            if not self.skip:
                isGenSeq = _isGenSeq(arg)
                if isGenSeq:
                    specs = {}
                    for hdl in _userCodeMap:
                        spec = "__%s__" % hdl
                        if spec in frame.f_locals and frame.f_locals[spec]:
                            specs[spec] = frame.f_locals[spec]
                        spec = "%s_code" % hdl
                        if func and hasattr(func, spec) and getattr(func, spec):
                            specs[spec] = getattr(func, spec)
                        spec = "%s_instance" % hdl
                        if func and hasattr(func, spec) and getattr(func, spec):
                            specs[spec] = getattr(func, spec)
                    if specs:
                        _addUserCode(specs, arg, funcname, func, frame)
                # building hierarchy only makes sense if there are generators
                if isGenSeq and arg:
                    sigdict = {}
                    memdict = {}
                    argdict = {}
                    if func:
                        arglist = inspect.getargspec(func).args
                    else:
                        arglist = []
                    symdict = frame.f_globals.copy()
                    symdict.update(frame.f_locals)
                    cellvars = []

                    # All nested functions will be in co_consts
                    if func:
                        local_gens = []
                        consts = func.__code__.co_consts
                        for item in _flatten(arg):
                            genfunc = _genfunc(item)
                            if genfunc.__code__ in consts:
                                local_gens.append(item)
                        if local_gens:
                            cellvarlist = _getCellVars(symdict, local_gens)
                            cellvars.extend(cellvarlist)
                            objlist = _resolveRefs(symdict, local_gens)
                            cellvars.extend(objlist)
                    #for dict in (frame.f_globals, frame.f_locals):
                    for n, v in symdict.items():
                        # extract signals and memories
                        # also keep track of whether they are used in generators
                        # only include objects that are used in generators
##                             if not n in cellvars:
##                                 continue
                        if isinstance(v, _Signal):
                            sigdict[n] = v
                            if n in cellvars:
                                v._markUsed()
                        if _isListOfSigs(v):
                            m = _makeMemInfo(v)
                            memdict[n] = m
                            if n in cellvars:
                                m._used = True
                        # save any other variable in argdict
                        if (n in arglist) and (n not in sigdict) and (n not in memdict):
                            argdict[n] = v

                    subs = []
                    for n, sub in frame.f_locals.items():
                        for elt in _inferArgs(arg):
                            if elt is sub:
                                subs.append((n, sub))

                    inst = _Instance(self.level, arg, subs, sigdict, memdict, func, argdict)
                    self.hierarchy.append(inst)

                self.level -= 1

            if funcname in self.skipNames:
                self.skip -= 1


def _inferArgs(arg):
    c = [arg]
    if isinstance(arg, (tuple, list)):
        c += list(arg)
    return c
