from __future__ import absolute_import
from __future__ import print_function

import platform

from . import __version__


def print_versions():
    versions = [
        ("myhdl", __version__),
        ("Python Version", platform.python_version()),
        ("Python Implementation", platform.python_implementation()),
        ("OS", platform.platform()),
    ]

    print()
    print("INSTALLED VERSIONS")
    print("------------------")
    for k, v in versions:
        print("{}: {}".format(k, v))


if __name__ == "__main__":
    print_versions()
