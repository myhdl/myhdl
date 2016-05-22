.. currentmodule:: myhdl

.. _unittest:

************
Unit testing
************


.. _unittest-intro:

Introduction
============

Many aspects in the design flow of modern digital hardware design can be viewed
as a special kind of software development. From that viewpoint, it is a natural
question whether advances in software design techniques can not also be applied
to hardware design.

.. index:: single: extreme programming

One software design approach that deserves attention is *Extreme Programming*
(XP). It is a fascinating set of techniques and guidelines that often seems to
go against the conventional wisdom. On other occasions, XP just seems to
emphasize the common sense, which doesn't always coincide with common practice.
For example, XP stresses the importance of normal workweeks, if we are to have
the fresh mind needed for good software development.

.. %

It is not my intention nor qualification to present a tutorial on Extreme
Programming. Instead, in this section I will highlight one XP concept which I
think is very relevant to hardware design: the importance and methodology of
unit testing.

.. _unittest-why:

The importance of unit tests
============================

Unit testing is one of the corner stones of Extreme Programming. Other XP
concepts, such as collective ownership of code and continuous refinement, are
only possible by having unit tests. Moreover, XP emphasizes that writing unit
tests should be automated, that they should test everything in every class, and
that they should run perfectly all the time.

I believe that these concepts apply directly to hardware design. In addition,
unit tests are a way to manage simulation time. For example, a state machine
that runs very slowly on infrequent events may be impossible to verify at the
system level, even on the fastest simulator. On the other hand, it may be easy
to verify it exhaustively in a unit test, even on the slowest simulator.

It is clear that unit tests have compelling advantages. On the other hand, if we
need to test everything, we have to write lots of unit tests. So it should be
easy and pleasant to create, manage and run them. Therefore, XP emphasizes the
need for a unit test framework that supports these tasks. In this chapter, we
will explore the use of the ``unittest`` module from the standard Python library
for creating unit tests for hardware designs.


.. _unittest-dev:

Unit test development
=====================

In this section, we will informally explore the application of unit test
techniques to hardware design. We will do so by a (small) example: testing a
binary to Gray encoder as introduced in section :ref:`hwtypes-indexing`.


.. _unittest-req:

Defining the requirements
-------------------------

We start by defining the requirements. For a Gray encoder, we want to the output
to comply with Gray code characteristics. Let's define a :dfn:`code` as a list
of :dfn:`codewords`, where a codeword is a bit string. A code of order ``n`` has
``2**n`` codewords.

A well-known characteristic is the one that Gray codes are all about:

*Consecutive codewords in a Gray code should differ in a single bit.*

Is this sufficient? Not quite: suppose for example that an implementation
returns the lsb of each binary input. This would comply with the requirement,
but is obviously not what we want. Also, we don't want the bit width of Gray
codewords to exceed the bit width of the binary codewords.

Each codeword in a Gray code of order n must occur exactly once in the binary
code of the same order.

With the requirements written down we can proceed.


.. _unittest-first:

Writing the test first
----------------------

A fascinating guideline in the XP world is to write the unit test first. That
is, before implementing something, first write the test that will verify it.
This seems to go against our natural inclination, and certainly against common
practices. Many engineers like to implement first and think about verification
afterwards.

But if you think about it, it makes a lot of sense to deal with verification
first. Verification is about the requirements only --- so your thoughts are not
yet cluttered with implementation details. The unit tests are an executable
description of the requirements, so they will be better understood and it will
be very clear what needs to be done. Consequently, the implementation should go
smoother. Perhaps most importantly, the test is available when you are done
implementing, and can be run anytime by anybody to verify changes.

Python has a standard ``unittest`` module that facilitates writing, managing and
running unit tests. With ``unittest``, a test case is  written by creating a
class that inherits from ``unittest.TestCase``. Individual tests are created by
methods of that class: all method names that start with ``test`` are considered
to be tests of the test case.

We will define a test case for the Gray code properties, and then write a test
for each of the requirements. The outline of the test case class is as follows::

   import unittest

   class TestGrayCodeProperties(unittest.TestCase):

       def testSingleBitChange(self):
        """Check that only one bit changes in successive codewords."""
        ....


       def testUniqueCodeWords(self):
       """Check that all codewords occur exactly once."""
       ....

Each method will be a small test bench that tests a single requirement. To write
the tests, we don't need an implementation of the Gray encoder, but we do need
the interface of the design. We can specify this by a dummy implementation, as
follows:

.. include-example:: bin2gray_dummy.py

For the first requirement, we will test all  consecutive input numbers, and
compare the current output with the previous one For each input, we check that
the difference is exactly a single bit. For the second requirement, we will test
all input numbers and put the result in a list. The requirement implies that if
we sort the result list, we should get a range of numbers. For both
requirements, we will test all Gray codes up to a certain order ``MAX_WIDTH``.
The test code looks as follows:

.. include-example:: test_gray_properties.py

Note how the actual check is performed by a ``self.assertEqual`` method, defined
by the ``unittest.TestCase`` class. Also, we have factored out running the
tests for all Gray codes in a separate method :func:`runTests`.

.. _unittest-impl:

Test-driven implementation
--------------------------

With the test written, we begin with the implementation. For illustration
purposes, we will intentionally write some incorrect implementations to see how
the test behaves.

The easiest way to run tests defined with the ``unittest`` framework, is to put
a call to its ``main`` method at the end of the test module::

   unittest.main()

Let's run the test using the dummy Gray encoder shown earlier::

  % python test_gray_properties.py
  testSingleBitChange (__main__.TestGrayCodeProperties)
  Check that only one bit changes in successive codewords. ... ERROR
  testUniqueCodeWords (__main__.TestGrayCodeProperties)
  Check that all codewords occur exactly once. ... ERROR

As expected, this fails completely. Let us try an incorrect implementation, that
puts the lsb of in the input on the output:

.. include-example:: bin2gray_wrong.py

Running the test produces::

  python test_gray_properties.py
  testSingleBitChange (__main__.TestGrayCodeProperties)
  Check that only one bit changes in successive codewords. ... ok
  testUniqueCodeWords (__main__.TestGrayCodeProperties)
  Check that all codewords occur exactly once. ... FAIL

  ======================================================================
  FAIL: testUniqueCodeWords (__main__.TestGrayCodeProperties)
  Check that all codewords occur exactly once.
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    File "test_gray_properties.py", line 42, in testUniqueCodeWords
      self.runTests(test)
    File "test_gray_properties.py", line 53, in runTests
      sim.run(quiet=1)
    File "/home/jand/dev/myhdl/myhdl/_Simulation.py", line 154, in run
      waiter.next(waiters, actives, exc)
    File "/home/jand/dev/myhdl/myhdl/_Waiter.py", line 127, in next
      clause = next(self.generator)
    File "test_gray_properties.py", line 40, in test
      self.assertEqual(actual, expected)
  AssertionError: Lists differ: [0, 0, 1, 1] != [0, 1, 2, 3]

  First differing element 1:
  0
  1

  - [0, 0, 1, 1]
  + [0, 1, 2, 3]

  ----------------------------------------------------------------------
  Ran 2 tests in 0.083s

  FAILED (failures=1)

Now the test passes the first requirement, as expected, but fails the second
one. After the test feedback, a full traceback is shown that can help to debug
the test output.

Finally, we use a correct implementation:

.. include-example:: bin2gray.py

Now the tests pass:

.. run-example:: test_gray_properties.py

.. _unittest-change:

Additional requirements
-----------------------

In the previous section, we concentrated on the general requirements of a Gray
code. It is possible to specify these without specifying the actual code. It is
easy to see that there are several codes that satisfy these requirements. In
good XP style, we only tested the requirements and nothing more.

It may be that more control is needed. For example, the requirement may be for a
particular code, instead of compliance with general properties. As an
illustration, we will show how to test for *the* original Gray code, which is
one specific instance that satisfies the requirements of the previous section.
In this particular case, this test will actually be easier than the previous
one.

We denote the original Gray code of order ``n`` as ``Ln``. Some examples::

   L1 = ['0', '1']
   L2 = ['00', '01', '11', '10']
   L3 = ['000', '001', '011', '010', '110', '111', '101', 100']

It is possible to specify these codes by a recursive algorithm, as follows:

#. L1 = ['0', '1']

#. Ln+1 can be obtained from Ln as follows. Create a new code Ln0 by prefixing
   all codewords of Ln with '0'. Create another new code Ln1 by prefixing all
   codewords of Ln with '1', and reversing their order. Ln+1 is the concatenation
   of Ln0 and Ln1.

Python is well-known for its elegant algorithmic descriptions, and this is a
good example. We can write the algorithm in Python as follows:

.. include-example:: next_gray_code.py

The code ``['0' + codeword for ...]`` is called a :dfn:`list comprehension`. It
is a concise way to describe lists built by short computations in a for loop.

The requirement is now that the output code matches the expected code Ln. We use
the ``nextLn`` function to compute the expected result. The new test case code
is as follows:

.. include-example:: test_gray_original.py

As it happens, our implementation is apparently an original Gray code:

.. run-example:: test_gray_original.py
