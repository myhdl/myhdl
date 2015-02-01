import sys

PY2 = sys.version_info[0] == 2


if not PY2:
    integer_types = (int,)
    long = int
    import builtins
else:
    integer_types = (int, long)
    long = long
    import __builtin__ as builtins
