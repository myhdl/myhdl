MyHDL Release 0.4.1
===================

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
change, an edge, a delay, or on the completion of another
generator. MyHDL supports waveform viewing by tracing signal changes
in a VCD file.

Python's rare combination of power and clarity makes it ideal for high
level modeling.  It can be expected that MyHDL users will often have
the ``Pythonic experience'' of finding an elegant solution to a
complex modeling problem. Moreover, Python is outstanding for rapid
application development and experimentation.

With MyHDL, the Python unit test framework can be used on hardware
designs.  MyHDL can also be used as hardware verification language for
VHDL and Verilog designs, by co-simulation with any simulator that has
a PLI.  The distribution contains a PLI module for the Icarus Verilog
simulator and for the cver Verilog simulator.

Finally, a subset of MyHDL code can be converted automatically to
synthesizable Verilog code. This feature provides a direct path from
Python to an FPGA or ASIC implementation.

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

You can test the proper installation as follows:
   
    cd myhdl/test
    python test_all.py

To install co-simulation support:

Go to the directory co-simulation/<platform> for your target platform
and following the instructions in the README.txt file.


DOCUMENTATION
-------------

See the doc/ subdirectory.


EXAMPLES
--------

See the example/ subdirectory for examples.


AUTHOR
------
Jan Decaluwe <jan@jandecaluwe.com>
