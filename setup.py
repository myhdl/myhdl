""" myhdl's distutils distribution and installation script. """

import sys

requiredVersion = (2, 6)
requiredVersionStr = ".".join([str(i) for i in requiredVersion])

versionError = "ERROR: myhdl requires Python %s or higher" % requiredVersionStr

# use version_info to check version
# this was new in 2.0, so first see if it exists
try:
    sys.version_info
except:
    print versionError
    raise SystemExit(1)

if sys.version_info < requiredVersion:
    print versionError
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
      version="0.8.1",
      description="Python as a Hardware Description Language",
      long_description = "See home page.",
      author="Jan Decaluwe",
      author_email="jan@jandecaluwe.com",
      url="http://www.myhdl.org",
      download_url="https://bitbucket.org/jandecaluwe/myhdl/get/0.8.zip",
      packages=['myhdl', 'myhdl.conversion'],
      license="LGPL",
      platforms=["Any"],
      keywords="HDL ASIC FPGA hardware design",
      classifiers=filter(None, classifiers.split("\n")),
      )
