********
Overview
********

The goal of the MyHDL project is to empower hardware designers with
the elegance and simplicity of the Python language.

MyHDL is a free, open-source package for using Python as a
hardware description and verification language. Python is a very high
level language, and hardware designers can use its full power to model
and simulate their designs.  Moreover, MyHDL can convert a design to
Verilog or VHDL. This provides a path into a traditional design flow.

*Modeling*

Python's power and clarity make MyHDL an ideal solution for high level
modeling.  Python is famous for enabling elegant solutions to complex
modeling problems.  Moreover, Python is outstanding for rapid
application development and experimentation.

The key idea behind MyHDL is the use of Python generators to model
hardware concurrency. Generators are best described as resumable
functions.  MyHDL generators are similar to always blocks in Verilog
and processes in VHDL.

A hardware module (called a *block* in MyHDL terminology) is modeled as a
function that returns generators. This approach makes it straightforward to
support features such as arbitrary hierarchy, named port association, arrays of
instances, and conditional instantiation.  Furthermore, MyHDL provides classes
that implement traditional hardware description concepts. It provides a signal
class to support communication between generators, a class to support bit
oriented operations, and a class for enumeration types.

*Simulation and Verification*

The built-in simulator runs on top of the Python interpreter. It supports
waveform viewing by tracing signal changes in a VCD file.

With MyHDL, the Python unit test framework can be used on hardware designs.
Although unit testing is a popular modern software verification technique, it is
still uncommon in the hardware design world.

MyHDL can also be used as hardware verification language for Verilog
designs, by co-simulation with traditional HDL simulators.

*Conversion to Verilog and VHDL*

Subject to some limitations, MyHDL designs can be converted to Verilog
or VHDL.  This provides a path into a traditional design flow,
including synthesis and implementation.  The convertible
subset is restricted, but much wider than the standard synthesis subset.
It includes features that can be used for high level modeling and test benches.

The converter works on an instantiated design that has been
fully elaborated. Consequently, the original design structure can be
arbitrarily complex. Moreover, the conversion limitations apply only
to code inside generators. Outside generators, Python's full power can
be used without compromising convertibility.

Finally, the converter automates a number of tasks that are hard in
Verilog or VHDL directly. A notable feature is the automated handling of
signed arithmetic issues.
