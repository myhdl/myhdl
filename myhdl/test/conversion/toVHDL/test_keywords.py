import myhdl
from myhdl import *
from myhdl import ToVHDLWarning

import pytest
import tempfile
import shutil
import sys
import string
import importlib
import os
from keyword import kwlist as python_kwlist

import warnings

_vhdl_keywords = ["abs", "access", "after", "alias", "all",
                  "and", "architecture", "array", "assert",
                  "attribute", "begin", "block", "body", "buffer",
                  "bus", "case", "component", "configuration",
                  "constant", "disconnect", "downto", "else",
                  "elseif", "end", "entity", "exit", "file", "for",
                  "function", "generate", "generic", "group",
                  "guarded", "if", "impure", "in", "inertial",
                  "inout", "is", "label", "library", "linkage",
                  "literal", "loop", "map", "mod", "nand", "new",
                  "next", "nor", "not", "null", "of", "on", "open",
                  "or", "others", "out", "package", "port",
                  "postponed", "procedure", "process", "pure",
                  "range", "record", "register", "reject", "rem",
                  "report", "return", "rol", "ror", "select",
                  "severity", "signal", "shared", "sla", "sll", "sra",
                  "srl", "subtype", "then", "to", "transport", "type",
                  "unaffected", "units", "until", "use", "variable",
                  "wait", "when", "while", "with", "xnor", "xor"];

keyword_code = """
from myhdl import *

@block
def invalid_import_keyword(input_sig, output_sig):
    ${keyword} = Signal(False)

    @always_comb
    def do_something():
        ${keyword}.next = input_sig and input_sig

    @always_comb
    def something_else():
        output_sig.next = ${keyword}

    return do_something, something_else
"""


@block
def invalid_signal_underscore(input_sig, output_sig):
    _foo = Signal(bool(0))

    @always_comb
    def do_something():
        _foo.next = input_sig and input_sig

    @always_comb
    def something_else():
        output_sig.next = _foo

    return do_something, something_else


@block
def invalid_function_underscore(clock, input_sig, output_sig):

    ttt = Signal(bool(0))

    block1 = invalid_signal_underscore(input_sig, ttt)

    @always(clock.posedge)
    def do_something():
        output_sig.next = ttt

    return block1, do_something


@block
def valid(input_sig, output_sig):

    @always_comb
    def do_something():
        output_sig.next = input_sig

    return do_something


def test_multiple_conversion():
    sig_1 = Signal(True)
    sig_2 = Signal(True)

    a_block = valid(sig_1, sig_2)

    # conversions with keyword should fail
    with warnings.catch_warnings() as w:
        warnings.simplefilter('error')

        a_block.convert(hdl='VHDL')
        a_block.convert(hdl='VHDL')


def test_invalid_keyword_name():
    sig_1 = Signal(True)
    sig_2 = Signal(True)

    temp_directory = tempfile.mkdtemp()
    sys.path.append(temp_directory)

    keyword_template = string.Template(keyword_code)

    try:
        for keyword in _vhdl_keywords:
            if keyword in python_kwlist:
                continue

            fd, full_filename = tempfile.mkstemp(
                suffix='.py', dir=temp_directory)

            os.write(fd, keyword_template.substitute(keyword=keyword).encode('utf-8'))
            os.close(fd)

            module_name = os.path.basename(full_filename)[:-3]  # chop off .py
            keyword_import = importlib.import_module(module_name)

            a_block = keyword_import.invalid_import_keyword(sig_1, sig_2)

            with pytest.warns(ToVHDLWarning):
                a_block.convert(hdl='VHDL')

    finally:
        sys.path.pop()
        shutil.rmtree(temp_directory)


def test_invalid_signal_underscore_name():
    sig_1 = Signal(True)
    sig_2 = Signal(True)

    a_block = invalid_signal_underscore(sig_1, sig_2)

    # Multiple conversions of a valid block should pass without warning
    with pytest.warns(ToVHDLWarning):
        a_block.convert(hdl='VHDL')


def test_invalid_function_underscore_name():
    sig_1 = Signal(True)
    sig_2 = Signal(True)
    clock = Signal(True)

    a_block = invalid_function_underscore(clock, sig_1, sig_2)

    # Multiple conversions of a valid block should pass without warning
    with pytest.warns(ToVHDLWarning):
        a_block.convert(hdl='VHDL')


if __name__ == '__main__':
    sig_1 = Signal(True)
    sig_2 = Signal(True)

    a_block = invalid_signal_underscore(sig_1, sig_2)
    a_block.convert(hdl='VHDL')

    clock = Signal(True)

    a_block = invalid_function_underscore(clock, sig_1, sig_2)

    # Multiple conversions of a valid block should pass without warning
    a_block.convert(hdl='VHDL')
