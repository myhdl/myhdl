""" myhdl's distribution and installation script. """

import sys

if sys.version_info < (2, 6) or (3, 0) <= sys.version_info < (3, 4):
    raise RuntimeError("Python version 2.6, 2.7 or >= 3.4 required.")


# Prefer setuptools over distutils
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="myhdl",
    version="0.9.dev0",
    description="Python as a Hardware Description Language",
    long_description="See home page.",
    author="Jan Decaluwe",
    author_email="jan@jandecaluwe.com",
    url="http://www.myhdl.org",
    download_url="https://bitbucket.org/jandecaluwe/myhdl/get/0.8.1.zip",
    packages=['myhdl', 'myhdl.conversion'],
    license="LGPL",
    platforms='any',
    keywords="HDL ASIC FPGA hardware design",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ]
)
