MyHDL Release 0.1
=================

INTRODUCTION
------------

MyHDL is a Python package for using Python as a hardware description
language. Popular hardware description languages, like Verilog and
VHDL, are compiled languages. MyHDL with Python could be viewed as a
"scripting language" counterpart of such languages. However, Python is
more accurately described as a very high level language (VHLL). MyHDL
users have access to the amazing power and elegance of Python in their
modeling work.

The key idea behind MyHDL is to use Python generators to model the
concurrency required in hardware descriptions. As generators are a
recent Python feature, MyHDL requires Python 2.2.2. or higher.

MyHDL 0.1 is the initial public release of the package. It can be used
to experiment with high level modeling, and with verification
techniques such as unit testing.

In a future release, MyHDL will hopefully be coupled to hardware
simulators for languages such as Verilog and VHDL. That would turn
MyHDL into a powerful hardware verification language.

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

    python test.py

DOCUMENTATION
-------------

See the doc/ subdirectory.

EXAMPLES
--------

See the example/ subdirectory for examples.

AUTHOR
------
Jan Decaluwe <jan@jandecaluwe.com>
