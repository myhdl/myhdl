MyHDL 0.8dev
============

What is MyHDL?
--------------
MyHDL is a free, open-source package for using Python as a hardware
description and verification language.

To find out whether MyHDL can be useful to you, please read:

    http://www.myhdl.org/doku.php/why

License
-------
MyHDL is available under the LGPL license.  See LICENSE.txt.

Website
-------
The project website is located at http://www.myhdl.org.

Documentation
-------------
The manual is available on-line:

   http://www.myhdl.org/doc/0.7/manual

What's new
----------
To find out what's new in this release, please read:

    http://www.myhdl.org/doc/0.7/whatsnew/0.7.html

Installation
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
Python library if necessary for more details;
or contact me.

You can test the proper installation as follows:
   
    cd myhdl/test/core
    python test_all.py

To install co-simulation support:

Go to the directory co-simulation/<platform> for your target platform
and following the instructions in the README.txt file.

