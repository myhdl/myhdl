import sys

PY2 = sys.version_info[0] == 2


if not PY2:
    string_types = (str,)
    integer_types = (int,)
    long = int

    from io import StringIO
    import builtins
else:
    string_types = (str, unicode)
    integer_types = (int, long)
    long = long

    from cStringIO import StringIO
    import __builtin__ as builtins
