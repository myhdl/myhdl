""" myhdl's distutils distribution and installation script. """

import sys

versionError = "ERROR: myhdl requires Python 2.2.2 or higher"

# use version_info to check version
# this was new in 2.0, so first see if it exists
try:
    sys.version_info
except:
    print versionError
    raise SystemExit(1)
# we need at least 2.2.2
if sys.version_info[:3] < (2, 2, 2):
    print versionError
    raise SystemExit(1)

from distutils.core import setup
    
setup(name="myhdl",
      version="0.3",
      description="Python as a Hardware Description Language",
      author="Jan Decaluwe",
      author_email="jan@jandecaluwe.com",
      url="http://jandecaluwe.com/Tools/MyHDL/Overview.html",
      download_url="http://jandecaluwe.com/Tools/MyHDL/Download.html",
      packages=['myhdl'],
      license="LGPL",
      )
      
