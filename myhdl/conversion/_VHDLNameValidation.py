import warnings
from myhdl import *
from myhdl import ToVHDLWarning

#A list of all reserved words within VHDL which should not be used for
#anything other than their own specific purpose
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

#A list to hold all signal names being used in lowercase to raise an error
#if no names are reused with different casing
_usedNames = [];

#Function which compares current parsed signal/entity to all keywords to
#ensure reserved words are not being used for the wrong purpose
def _nameValid(name):
    for keyword in _vhdl_keywords:
        if name == keyword:
            warnings.warn("VHDL keyword used: %s" % (name), category=ToVHDLWarning)
    for saved_name in _usedNames:
        if name.lower() == saved_name:
            warnings.warn("Previously used name being reused: %s" % (name), category=ToVHDLWarning)
    _usedNames.append(name.lower())
    if name[0] == '_':
        warnings.warn("VHDL variable names cannot contain '_': %s" % (name), category=ToVHDLWarning)
    for char in name:
        if char == '-':
            warnings.warn("VHDL variable names cannot contain '-': %s" % (name), category=ToVHDLWarning)
