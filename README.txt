MyHDL Release 0.2
=================

INTRODUCTION
------------

MyHDL is a Python package for using Python as a hardware description
language. Popular hardware description languages, like Verilog and
VHDL, are compiled languages. MyHDL with Python can be viewed as a
"scripting language" counterpart of such languages. However, Python is
more accurately described as a very high level language
(VHLL). MyHDL users have access to the amazing power and elegance of
Python for their modeling work.

The key idea behind MyHDL is to use Python generators to model the
concurrency required in hardware descriptions. As generators are a
recent Python feature, MyHDL requires Python 2.2.2 or higher.

MyHDL can be used to experiment with high level modeling, and with
verification techniques such as unit testing. The most important
practical application however, is to use it as a hardware verification
language by co-simulation with Verilog and VHDL.

The present release, MyHDL 0.2, enables MyHDL for
co-simulation. The MyHDL side is designed to work with any simulator
that has a PLI. For each simulator, an appropriate PLI module in C
needs to be provided. The release contains such a module for the
Icarus Verilog simulator.


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
