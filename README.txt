myhdl Release 0.1
=================

INTRODUCTION
------------

myhdl is a Python package for using Python as a hardware description
language. Popular hardware description languages, like Verilog and
VHDL, are compiled languages. myhdl with Python can be viewed as a
"scripting language" counterpart of such languages.

The key idea behind myhdl is to use Python generators to model the
concurrency required in hardware descriptions. As generators are a
recent Python feature, you will need Python 2.2.2. or higher.

INSTALLATION
------------

If you have superuser power, you can install myhdl as follows:

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
