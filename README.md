MyHDL 0.11 
==========

This is an UNSTABLE development branch for testing only.
There are attempts to fix a few flaws and use an alternate testing approach, plus a few features (work in progress):


- Verified correct sign extension in VHDL conversion (consistency with MyHDL simulation)
- Named slice subscript support for improved readability
- Verified correctness for VHDL-93 and VHDL-08 standards


Currently no tests are done, as most classic tests are failing with my current GHDL setup (which is differing from the official test suite by yet unknown parameters). When the commits start to be marked by continuous integration, development is considered stable.

The reason for this new approach is to keep complex legacy code from an enhanced stable 0.9 release supported.
This is following a rather strict verification procedure from another component that is using MyHDL.

The primary goal is, to improve the VHDL conversion tests, then later see how this corresponds to Verilog support.


------------------------

What is MyHDL?
--------------
MyHDL is a free, open-source package for using Python as a hardware
description and verification language.

To find out whether MyHDL can be useful to you, please read:

   - http://www.myhdl.org/start/why.html

License
-------
MyHDL is available under the LGPL license.  See ``LICENSE.txt``.

Website
-------
The project website is located at http://www.myhdl.org

Documentation
-------------
The manual is available on-line:

   - http://docs.myhdl.org/en/stable/manual

What's new
----------
To find out what's new in this release, please read:

   - http://docs.myhdl.org/en/stable/whatsnew/0.11.html

Installation
------------
It is recommended to install MyHDL (and your project's other dependencies) in
a virtualenv.

Installing the latest stable release:

```
pip install myhdl
```

To install the development version from github:
```
pip install -e 'git+https://github.com/myhdl/myhdl#egg=myhdl
```

To install a local clone of the repository:
```
pip install -e path/to/dir
```

To install a specific commit hash, tag or branch from git:
```
pip install -e 'git+https://github.com/myhdl/myhdl@f696b8#egg=myhdl
```


You can test the proper installation as follows:

```
cd myhdl/test/core
py.test
```

To install co-simulation support:

Go to the directory ``cosimulation/<platform>`` for your target platform
and following the instructions in the ``README.txt`` file.
