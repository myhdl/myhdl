import sys

PY2 = sys.version_info[0] == 2


if not PY2:
    integer_types = (int,)
else:
    integer_types = (int, long)
