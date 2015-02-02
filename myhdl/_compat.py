import sys
import types

PY2 = sys.version_info[0] == 2


if not PY2:
    string_types = (str,)
    integer_types = (int,)
    long = int
    class_types = (type,)

    from io import StringIO
    import builtins
else:
    string_types = (str, unicode)
    integer_types = (int, long)
    long = long
    class_types = (type, types.ClassType)

    from cStringIO import StringIO
    import __builtin__ as builtins
