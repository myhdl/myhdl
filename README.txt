MyHDL Release 0.3
=================

INTRODUCTION
------------

MyHDL is a Python package for using Python as a hardware description
and verification language. Languages such Verilog and VHDL are
compiled languages. Python with MyHDL can be viewed as a "scripting
language" counterpart of such languages. However, Python is more
accurately described as a very high level language (VHLL). MyHDL users
have access to the amazing power and elegance of Python.

The key idea behind MyHDL is to use Python generators for modeling
hardware concurrency. A generator is a resumable function with
internal state. In MyHDL, a hardware module is modeled as a function
that returns generators. With this approach, MyHDL directly supports
features such as named port association, arrays of instances, and
conditional instantiation.

MyHDL supports the classic hardware description concepts. It provides
a signal class similar to the VHDL signal, a class for bit oriented
operations, and support for enumeration types.  The Python yield
statement is used as a general sensitivity list to wait on a signal
change, an edge, a delay, or on another generator. MyHDL supports
waveform viewing by tracing signal changes in a VCD file.

High level modeling is the ideal application of MyHDL and Python. The
possibilities are extensive and beyond the scope of most other
languages. It can be expected that MyHDL users will often have the
``Pythonic experience'' of finding an elegant solution to a complex
modeling problem.

With MyHDL, the Python unit test framework can be used on hardware
designs.  MyHDL can also be used as hardware verification language for
VHDL and Verilog designs, by co-simulation with any simulator that has
a PLI.  The distribution contains a PLI module for the Icarus Verilog
simulator.

The MyHDL software is open source software. It is licensed under the
GNU Lesser General Public License (LGPL).


INSTALLATION
------------

If you have superuser power, you can install MyHDL as follows:

    python setup.py install

This will install the package in the appropriate site-wide Python
package location.

Otherwise, you can install it in a personal directory, e.g. as
follows: 

    python setup.py install --home=$HOME

In this case, be sure to add the appropriate install dir to the
$PYTHONPATH. 

If necessary, consult the distutils documentation in the standard
Python library if necessary for more details; or contact me.

You can test the installation as follows:
   
    cd test
    python test.py

To install co-simulation support:

Go to the directory co-simulation/<platform> for your target platform
and following the instructions in the README.txt file. Currently, the
only supported platform is Icarus.


DOCUMENTATION
-------------

See the doc/ subdirectory.


EXAMPLES
--------

See the example/ subdirectory for examples.


AUTHOR
------
Jan Decaluwe <jan@jandecaluwe.com>
