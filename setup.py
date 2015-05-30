""" myhdl's distribution and installation script. """

<<<<<<< HEAD
from __future__ import print_function
=======
import ast
import fnmatch
import re
import os
>>>>>>> 846f7ad444059d0ca33d36f10adb2214223129f5
import sys

from collections import defaultdict

if sys.version_info < (2, 6) or (3, 0) <= sys.version_info < (3, 4):
    raise RuntimeError("Python version 2.6, 2.7 or >= 3.4 required.")


# Prefer setuptools over distutils
try:
<<<<<<< HEAD
    sys.version_info
except:
    print(versionError)
    raise SystemExit(1)

if sys.version_info < requiredVersion:
    print(versionError)
    raise SystemExit(1)

from distutils.core import setup

classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)
Operating System :: OS Independent
Programming Language :: Python
Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)
"""

    
setup(name="myhdl",
      version="0.9",
      description="Python as a Hardware Description Language",
      long_description = "See home page.",
      author="Jan Decaluwe",
      author_email="jan@jandecaluwe.com",
      url="http://www.myhdl.org",
      download_url="https://bitbucket.org/jandecaluwe/myhdl/get/0.8.1.zip",
      packages=['myhdl', 'myhdl.conversion'],
      license="LGPL",
      platforms=["Any"],
      keywords="HDL ASIC FPGA hardware design",
      classifiers=filter(None, classifiers.split("\n")),
      )
=======
    from setuptools import setup
except ImportError:
    from distutils.core import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('myhdl/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

data_root = 'share/myhdl'
cosim_data = defaultdict(list)
for base, dir, files in os.walk('cosimulation'):
    for pat in ('*.c', 'Makefile*', '*.py', '*.v', '*.txt'):
        good = fnmatch.filter(files, pat)
        if good:
            cosim_data[base].extend(os.path.join(base, f) for f in good)

setup(
    name="myhdl",
    version=version,
    description="Python as a Hardware Description Language",
    long_description="See home page.",
    author="Jan Decaluwe",
    author_email="jan@jandecaluwe.com",
    url="http://www.myhdl.org",
    packages=['myhdl', 'myhdl.conversion'],
    data_files=[(os.path.join(data_root, k), v) for k, v in cosim_data.items()],
    license="LGPL",
    platforms='any',
    keywords="HDL ASIC FPGA hardware design",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ]
)
>>>>>>> 846f7ad444059d0ca33d36f10adb2214223129f5
