The examples in this directory are based on VHDL code from the
"arith_lib" library, Version 1.0, written by Reto Zimmerman, who holds
the copyright for the original code. The project web page is at
<http://www.iis.ee.ethz.ch/~zimmi/arith_lib.html>.

I translated a few modules into myhdl/Python and added testbenches to
verify and demonstrate myhdl modeling, as well as Python's unit test
framework. The arith_lib library is useful for these purposes as it
contains a (simple) behavioral architecture as well as a (sometimes
complex) structural architecture for each module.

The testbenches are the files called test_<Name>.py. Run them as
follows:

    python test_<Name>.py


