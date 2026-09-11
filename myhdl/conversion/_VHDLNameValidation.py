import warnings
# from myhdl import *

from myhdl import ToVHDLWarning

# A list of all reserved words within VHDL which should not be used for
# anything other than their own specific purpose
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

# A list to hold all (namespace, name) pairs being used, with the name in
# lowercase, to raise an error if names are reused with different casing
_usedNames = [];


# Function which compares current parsed signal/entity to all keywords to
# ensure reserved words are not being used for the wrong purpose.
# Enum literals are checked in the namespace of their enum type: VHDL allows
# literals of different enum types to share a name, but not a literal and
# any other declaration (which are all in the root namespace).
def _nameValid(name, namespace=None):
    if name.lower() in _vhdl_keywords:
        warnings.warn(
            "VHDL keyword used: {}".format(name), category=ToVHDLWarning)

    if name.startswith('_'):
        warnings.warn(
            "VHDL variable names cannot start with '_': {}".format(name),
            category=ToVHDLWarning)

    if '-' in name:
        warnings.warn(
            "VHDL variable names cannot contain '-': {}".format(name),
            category=ToVHDLWarning)

    if '__' in name:
        warnings.warn(
            "VHDL variable names cannot contain double underscores '__': "
            "{}".format(name), category=ToVHDLWarning)

    name_key = (namespace, name.lower())
    if name_key in _usedNames:
        if namespace is None:
            warnings.warn(
                "Previously used name being reused in root namespace: {}".format(
                    name), category=ToVHDLWarning)
        else:
            warnings.warn(
                "Previously used name being reused in namespace {}: {}".format(
                    namespace, name), category=ToVHDLWarning)

    elif namespace is None:
        for used_namespace, used_name in _usedNames:
            if used_name == name_key[1]:
                warnings.warn(
                    "Name clashes with an enum literal in namespace {}: "
                    "{}".format(used_namespace, name), category=ToVHDLWarning)
                break

    elif (None, name_key[1]) in _usedNames:
        warnings.warn(
            "Enum literal in namespace {} clashes with a name in root "
            "namespace: {}".format(namespace, name), category=ToVHDLWarning)

    _usedNames.append(name_key)

