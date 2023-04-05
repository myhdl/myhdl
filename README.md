MyHDL 0.11 
==========

[![Join the chat at https://gitter.im/myhdl/myhdl](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/myhdl/myhdl?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Visit Discourse](https://www.clipartmax.com/png/small/208-2081333_discourse-meta-discourse-logo.png)](https://discourse.myhdl.org)

[![Documentation Status](https://readthedocs.org/projects/myhdl/badge/?version=stable)](http://docs.myhdl.org/en/stable/manual/)
[![Documentation Status](https://readthedocs.org/projects/myhdl/badge/?version=latest)](http://docs.myhdl.org/en/latest/manual)

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
Unfortunately version the PyPI is quite behind the current development status, so you are better off installing the *stable* master branch directly from this GitHub repository:

```
pip install git+https://github.com/myhdl/myhdl.git@master
```

To install a local clone of the repository:

```
pip install -e path/to/dir
```

To install a specific commit hash, tag or branch from git:

```
pip install git+https://github.com/myhdl/myhdl@f696b8
```


You can test the proper installation as follows:

```
cd myhdl/test/core
py.test
```

To install co-simulation support:

Go to the directory ``cosimulation/<platform>`` for your target platform
and following the instructions in the ``README.txt`` file.
