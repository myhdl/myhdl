.. currentmodule:: myhdl


.. _model:

*******************
Modeling techniques
*******************


.. _model-structure:

Structural modeling
===================

.. index:: single: modeling; structural

Hardware descriptions need to support the concepts of module instantiation and
hierarchy.  In MyHDL, an instance is recursively defined as being either a
sequence of instances, or a generator. Hierarchy is modeled by defining
instances in a higher-level function, and returning them.  The following is a
schematic example of the basic case. ::

   def top(...):
       ...
       instance_1 = module_1(...)
       instance_2 = module_2(...)
       ...
       instance_n = module_n(...)
       ... 
       return instance_1, instance_2, ... , instance_n

Note that MyHDL uses conventional procedural techniques for modeling structure.
This makes it straightforward to model more complex cases.


.. _model-conf:

Conditional instantiation
-------------------------

.. index:: single: conditional instantiation

To model conditional instantiation, we can select the returned instance under
parameter control. For example::

   SLOW, MEDIUM, FAST = range(3)

   def top(..., speed=SLOW):
       ...
       def slowAndSmall():
          ...
       ...
       def fastAndLarge():
          ...
       if speed == SLOW:
           return slowAndSmall()
       elif speed == FAST:
           return fastAndLarge()
       else:
           raise NotImplementedError


.. _model-instarray:

Lists of instances and signals
------------------------------

.. index:: single: lists of instances and signals

Python lists are easy to create. We can use them to model lists of instances.

Suppose we have a top module that instantiates a single ``channel`` submodule,
as follows::

   def top(...):

       din = Signal(0)
       dout = Signal(0)
       clk = Signal(bool(0))
       reset = Signal(bool(0))

       channel_inst = channel(dout, din, clk, reset)

       return channel_inst 

If we wanted to support an arbitrary number of channels, we can use lists of
signals and a list of instances, as follows::

   def top(..., n=8):

       din = [Signal(0) for i in range(n)]
       dout = [Signal(0) for in range(n)]
       clk = Signal(bool(0))
       reset = Signal(bool(0))
       channel_inst = [None for i in range(n)]

       for i in range(n):
           channel_inst[i] = channel(dout[i], din[i], clk, reset)

       return channel_inst

.. _model-shadow-signals:

Converting between lists of signals and bit vectors
---------------------------------------------------

Compared to HDLs such as VHDL and Verilog, MyHDL signals are less
flexible for structural modeling. For example, slicing a signal
returns a slice of the current value. For behavioral code, this is
just fine. However, it implies that you cannot use such as slice in
structural descriptions. In other words, a signal slice cannot be used
as a signal.

In MyHDL, you can address such cases by a concept called
shadow signals. A shadow signal is constructed out of
other signals and follows their value changes automatically.
For example, a :class:`_SliceSignal` follows the value of
an index or a slice from another signal.  Likewise, 
A :class:`ConcatSignal` follows the
values of a number of signals as a concatenation.

As an example, suppose we have a system with N requesters that
need arbitration. Each requester has a ``request`` output
and a ``grant`` input. To connect them in the system, we can
use list of signals. For example, a list of request signals
can be constructed as follows::

    request_list = [Signal(bool()) for i in range(M)]

Suppose that an arbiter module is available that is
instantiated as follows::

    arb = arbiter(grant_vector, request_vector, clock, reset)

The ``request_vector`` input is a bit vector that can have
any of its bits asserted. The ``grant_vector`` is an output
bit vector with just a single bit asserted, or none.
Such a module is typically based on bit vectors because
they are easy to process in RTL code. In MyHDL, a bit vector
is modeled using the :class:`intbv` type.

We need a way to "connect" the list of signals to the 
bit vector and vice versa. Of course, we can do this with explicit
code, but shadow signals can do this automatically. For
example, we can construct a ``request_vector`` as a
:class:`ConcatSignal` object::

    request_vector = ConcatSignal(*reversed(request_list)

Note that we reverse the list first. This is done because the index range
of lists is the inverse of the range of :class:`intbv` bit vectors.
By reversing, the indices correspond to the same bit.

The inverse problem exist for the ``grant_vector``. It would be defined as follows::

    grant_vector = Signal(intbv(0)[M:])

To construct a list of signals that are connected automatically to the
bit vector, we can use the :class:`Signal` call interface to construct
:class:`_SliceSignal` objects::

    grant_list = [grant_vector(i) for i in range(M)]

Note the round brackets used for this type of slicing. Also, it may not be
necessary to construct this list explicitly. You can simply use
``grant_vector(i)`` in an instantation.

To decide when to use normal or shadow signals, consider the data
flow. Use normal signals to connect to *outputs*. Use shadow signals to
transform these signals so that they can be used as *inputs*.


.. _model-infer-instlist:

Inferring the list of instances
-------------------------------

In MyHDL, instances have to be returned explicitly by a top level function. It
may be convenient to assemble  the list of instances automatically. For this
purpose, MyHDL  provides the function :func:`instances`. Using the first example
in this section, it is used as follows::

   from myhdl import instances

   def top(...):
       ...
       instance_1 = module_1(...)
       instance_2 = module_2(...)
       ...
       instance_n = module_n(...)
       ...
       return instances()

Function :func:`instances` uses introspection to inspect the type of the local
variables defined by the calling function. All variables that comply with the
definition of an instance are assembled in a list, and that list is returned.


.. _model-rtl:

RTL modeling
============

.. index:: single: modeling; RTL style

The present section describes how MyHDL supports RTL style modeling as is
typically used for synthesizable models.


.. _model-comb:

Combinatorial logic
-------------------

.. index:: single: combinatorial logic


.. _model-comb-templ:

Template
^^^^^^^^

Combinatorial logic is described with a code pattern as follows::

   def top(<parameters>):
       ...
       @always_comb
       def combLogic():
           <functional code>
       ...
       return combLogic, ...

The :func:`always_comb` decorator describes combinatorial logic.  [#]_. The
decorated function is a local function that specifies what happens when one of
the input signals of the logic changes.  The :func:`always_comb` decorator
infers the input signals automatically. It returns a generator that is sensitive
to all inputs, and that executes the function whenever an input changes.


.. _model-comb-ex:

Example
^^^^^^^

The following is an example of a combinatorial multiplexer::

   from myhdl import Signal, Simulation, delay, always_comb

   def Mux(z, a, b, sel):

       """ Multiplexer.

       z -- mux output
       a, b -- data inputs
       sel -- control input: select a if asserted, otherwise b

       """

       @always_comb
       def muxLogic():
           if sel == 1:
               z.next = a
           else:
               z.next = b

       return muxLogic

To verify it, we will simulate the logic with some random patterns. The
``random`` module in Python's standard library comes in handy for such purposes.
The function ``randrange(n)`` returns a random natural integer smaller than *n*.
It is used in the test bench code to produce random input values::

   from random import randrange

   z, a, b, sel = [Signal(0) for i in range(4)]

   mux_1 = Mux(z, a, b, sel)

   def test():
       print "z a b sel"
       for i in range(8):
           a.next, b.next, sel.next = randrange(8), randrange(8), randrange(2)
           yield delay(10)
           print "%s %s %s %s" % (z, a, b, sel)

   test_1 = test()

   sim = Simulation(mux_1, test_1)
   sim.run()    

Because of the randomness, the simulation output varies between runs  [#]_. One
particular run produced the following output::

   % python mux.py
   z a b sel
   6 6 1 1
   7 7 1 1
   7 3 7 0
   1 2 1 0
   7 7 5 1
   4 7 4 0
   4 0 4 0
   3 3 5 1
   StopSimulation: No more events


.. _model-seq:

Sequential logic
----------------

.. index:: single: sequential logic


.. _model-seq-templ:

Template
^^^^^^^^

Sequential RTL models are sensitive to a clock edge. In addition, they may be
sensitive to a reset signal. We will describe one of the most common patterns: a
template with a rising clock edge and an asynchronous reset signal. Other
templates are similar. ::

   def top(<parameters>, clock, ..., reset, ...):
       ...
       @always(clock.posedge, reset.negedge)
       def seqLogic():
           if reset == <active level>:
               <reset code>
           else:
               <functional code>
       ...
       return seqLogic, ...


.. _model-seq-ex:

Example
^^^^^^^

The following code is a description of an incrementer with enable, and an
asynchronous reset. ::

   from random import randrange
   from myhdl import *

   ACTIVE_LOW, INACTIVE_HIGH = 0, 1

   def Inc(count, enable, clock, reset, n):

       """ Incrementer with enable.

       count -- output
       enable -- control input, increment when 1
       clock -- clock input
       reset -- asynchronous reset input
       n -- counter max value

       """

       @always(clock.posedge, reset.negedge)
       def incLogic():
           if reset == ACTIVE_LOW:
               count.next = 0
           else:
               if enable:
                   count.next = (count + 1) % n

       return incLogic

For the test bench, we will use an independent clock generator, stimulus
generator, and monitor. After applying enough stimulus patterns, we can raise
the ``StopSimulation`` exception to stop the simulation run. The test bench for
a small incrementer and a small number of patterns is a follows::

   def testbench():
       count, enable, clock, reset = [Signal(intbv(0)) for i in range(4)]

       inc_1 = Inc(count, enable, clock, reset, n=4)

       HALF_PERIOD = delay(10)

       @always(HALF_PERIOD)
       def clockGen():
           clock.next = not clock

       @instance
       def stimulus():
           reset.next = ACTIVE_LOW
           yield clock.negedge
           reset.next = INACTIVE_HIGH
           for i in range(12):
               enable.next = min(1, randrange(3))
               yield clock.negedge
           raise StopSimulation

       @instance
       def monitor():
           print "enable  count"
           yield reset.posedge
           while 1:
               yield clock.posedge
               yield delay(1)
               print "   %s      %s" % (enable, count)

       return clockGen, stimulus, inc_1, monitor


   tb = testbench()

   def main():
       Simulation(tb).run()

The simulation produces the following output::

   % python inc.py
   enable  count
      0      0
      1      1
      0      1
      1      2
      1      3
      1      0
      0      0
      1      1
      0      1
      0      1
      0      1
      1      2
   StopSimulation


.. _model-fsm:

Finite State Machine modeling
-----------------------------

.. index:: single: modeling; Finite State Machine

Finite State Machine (FSM) modeling is very common in RTL design and therefore
deserves special attention.

For code clarity, the state values are typically represented by a set of
identifiers. A standard Python idiom for this purpose is to assign a range of
integers to a tuple of identifiers, like so::

   >>> SEARCH, CONFIRM, SYNC = range(3)
   >>> CONFIRM
   1

However, this technique has some drawbacks. Though it is clearly the intention
that the identifiers belong together, this information is lost as soon as they
are defined. Also, the identifiers evaluate to integers, whereas a string
representation of the identifiers would be preferable. To solve these issues, we
need an *enumeration type*.

.. index:: single: enum(); example usage

MyHDL supports enumeration types by providing a function :func:`enum`.  The
arguments to :func:`enum` are the string representations of the identifiers, and
its return value is an enumeration type. The identifiers are available as
attributes of the type. For example::

   >>> from myhdl import enum
   >>> t_State = enum('SEARCH', 'CONFIRM', 'SYNC')
   >>> t_State
   <Enum: SEARCH, CONFIRM, SYNC>
   >>> t_State.CONFIRM
   CONFIRM

We can use this type to construct a state signal as follows::

   state = Signal(t_State.SEARCH)

As an example, we will use a framing controller FSM.  It is an imaginary
example, but similar control structures are often found in telecommunication
applications. Suppose that we need to find the Start Of Frame (SOF) position of
an incoming frame of bytes. A sync pattern detector continuously looks for a
framing pattern and indicates it to the FSM with a ``syncFlag`` signal. When
found, the FSM moves from the initial ``SEARCH`` state to the ``CONFIRM`` state.
When the ``syncFlag`` is confirmed on the expected position, the FSM declares
``SYNC``, otherwise it falls back to the ``SEARCH`` state.  This FSM can be
coded as follows::

   from myhdl import *

   ACTIVE_LOW = 0
   FRAME_SIZE = 8
   t_State = enum('SEARCH', 'CONFIRM', 'SYNC')

   def FramerCtrl(SOF, state, syncFlag, clk, reset_n):

       """ Framing control FSM.

       SOF -- start-of-frame output bit
       state -- FramerState output
       syncFlag -- sync pattern found indication input
       clk -- clock input
       reset_n -- active low reset

       """

       index = Signal(0) # position in frame

       @always(clk.posedge, reset_n.negedge)
       def FSM():
           if reset_n == ACTIVE_LOW:
               SOF.next = 0
               index.next = 0
               state.next = t_State.SEARCH

           else:
               index.next = (index + 1) % FRAME_SIZE
               SOF.next = 0

               if state == t_State.SEARCH:
                   index.next = 1
                   if syncFlag:
                       state.next = t_State.CONFIRM

               elif state == t_State.CONFIRM:
                   if index == 0:
                       if syncFlag:
                           state.next = t_State.SYNC
                       else:
                           state.next = t_State.SEARCH

               elif state == t_State.SYNC:
                   if index == 0:
                       if not syncFlag:
                           state.next = t_State.SEARCH
                   SOF.next = (index == FRAME_SIZE-1)

               else:
                   raise ValueError("Undefined state")

       return FSM

.. index:: single: waveform viewing

At this point, we will use the example to demonstrate the MyHDL support for
waveform viewing. During simulation, signal changes can be written to a VCD
output file.  The VCD file can then be loaded and viewed in a waveform viewer
tool such as :program:`gtkwave`.

.. % 

The user interface of this feature consists of a single function,
:func:`traceSignals`.  To explain how it works, recall that in MyHDL, an
instance is created by assigning the result of a function call to an instance
name. For example::

   tb_fsm = testbench()

To enable VCD tracing, the instance should be created as follows instead::

   tb_fsm = traceSignals(testbench)

Note that the first argument of :func:`traceSignals` consists of the uncalled
function. By calling the function under its control, :func:`traceSignals`
gathers information about the hierarchy and the signals to be traced. In
addition to a function argument, :func:`traceSignals` accepts an arbitrary
number of non-keyword and keyword arguments that will be passed to the function
call.

A small test bench for our framing controller example, with signal tracing
enabled, is shown below::

   def testbench():

       SOF = Signal(bool(0))
       syncFlag = Signal(bool(0))
       clk = Signal(bool(0))
       reset_n = Signal(bool(1))
       state = Signal(t_State.SEARCH)

       framectrl = FramerCtrl(SOF, state, syncFlag, clk, reset_n)

       @always(delay(10))
       def clkgen():
           clk.next = not clk

       @instance
       def stimulus():
           for i in range(3):
               yield clk.posedge
           for n in (12, 8, 8, 4):
               syncFlag.next = 1
               yield clk.posedge
               syncFlag.next = 0
               for i in range(n-1):
                   yield clk.posedge
           raise StopSimulation

       return framectrl, clkgen, stimulus


   tb_fsm = traceSignals(testbench)
   sim = Simulation(tb_fsm)
   sim.run()

When we run the test bench, it generates a VCD file called
:file:`testbench.vcd`. When we load this file into :program:`gtkwave`, we can
view the waveforms:

.. image:: tbfsm.png

Signals are dumped in a suitable format. This format is inferred at the
:class:`Signal` construction time, from the type of the initial value. In
particular, :class:`bool` signals are dumped as single bits. (This only works
starting with Python 2.3, when :class:`bool` has become a separate type).
Likewise, :class:`intbv` signals with a defined bit width are dumped as bit
vectors. To support the general case, other types of signals are dumped as a
string representation, as returned by the standard :func:`str` function.

.. warning::

   Support for literal string representations is not part of the VCD standard. It
   is specific to :program:`gtkwave`. To generate a standard VCD file, you need to
   use signals with a defined bit width only.


.. _model-hl:

High level modeling
===================

.. index:: single: modeling; high level


.. _model-bfm:

Modeling with bus-functional procedures
---------------------------------------

.. index:: single: bus-functional procedure

A :dfn:`bus-functional procedure` is a reusable encapsulation of the low-level
operations needed to implement some abstract transaction on a physical
interface. Bus-functional procedures are typically used in flexible verification
environments.

.. % 

Once again, MyHDL uses generator functions to support bus-functional procedures.
In MyHDL, the difference between instances and bus-functional procedure calls
comes from the way in which a generator function is used.

As an example, we will design a bus-functional procedure of a simplified UART
transmitter. We assume 8 data bits, no parity bit, and a single stop bit, and we
add print statements to follow the simulation behavior::

   T_9600 = int(1e9 / 9600)

   def rs232_tx(tx, data, duration=T_9600):

       """ Simple rs232 transmitter procedure.

       tx -- serial output data
       data -- input data byte to be transmitted
       duration -- transmit bit duration

       """

       print "-- Transmitting %s --" % hex(data)
       print "TX: start bit"      
       tx.next = 0
       yield delay(duration)

       for i in range(8):
           print "TX: %s" % data[i]
           tx.next = data[i]
           yield delay(duration)

       print "TX: stop bit"      
       tx.next = 1
       yield delay(duration)

This looks exactly like the generator functions in previous sections. It becomes
a bus-functional procedure when we use it differently. Suppose that in a test
bench, we want to generate a number of data bytes to be transmitted. This can be
modeled as follows::

   testvals = (0xc5, 0x3a, 0x4b)

   def stimulus():
       tx = Signal(1)
       for val in testvals:
           txData = intbv(val)
           yield rs232_tx(tx, txData)

.. index:: single: wait; for the completion of a generator

We use the bus-functional procedure call as a clause in a ``yield`` statement.
This introduces a fourth form of the ``yield`` statement: using a generator as a
clause. Although this is a more dynamic usage than in the previous cases, the
meaning is actually very similar: at that point, the original generator should
wait for the completion of a generator.  In this case, the original generator
resumes when the ``rs232_tx(tx, txData)`` generator returns.

.. % 

When simulating this, we get::

   -- Transmitting 0xc5 --
   TX: start bit
   TX: 1
   TX: 0
   TX: 1
   TX: 0
   TX: 0
   TX: 0
   TX: 1
   TX: 1
   TX: stop bit
   -- Transmitting 0x3a --
   TX: start bit
   TX: 0
   TX: 1
   TX: 0
   TX: 1
   ...

We will continue with this example by designing the corresponding UART receiver
bus-functional procedure. This will allow us to introduce further capabilities
of MyHDL and its use of the ``yield`` statement.

.. index:: single: sensitivity list

Until now, the ``yield`` statements had a single clause. However, they can have
multiple clauses as well. In that case, the generator resumes as soon as the
wait condition specified by one of the clauses is satisfied. This corresponds to
the functionality of sensitivity lists in Verilog and VHDL.

.. % 

For example, suppose we want to design an UART receive procedure with a timeout.
We can specify the timeout condition while waiting for the start bit, as in the
following generator function::

   def rs232_rx(rx, data, duration=T_9600, timeout=MAX_TIMEOUT):

       """ Simple rs232 receiver procedure.

       rx -- serial input data
       data -- data received
       duration -- receive bit duration

       """

       # wait on start bit until timeout
       yield rx.negedge, delay(timeout)
       if rx == 1:
           raise StopSimulation, "RX time out error"

       # sample in the middle of the bit duration
       yield delay(duration // 2)
       print "RX: start bit"

       for i in range(8):
           yield delay(duration)
           print "RX: %s" % rx
           data[i] = rx

       yield delay(duration)
       print "RX: stop bit"
       print "-- Received %s --" % hex(data)

If the timeout condition is triggered, the receive bit ``rx`` will still be
``1``. In that case, we raise an exception to stop the simulation. The
``StopSimulation`` exception is predefined in MyHDL for such purposes. In the
other case, we proceed by positioning the sample point in the middle of the bit
duration, and sampling the received data bits.

When a ``yield`` statement has multiple clauses, they can be of any type that is
supported as a single clause, including generators. For example, we can verify
the transmitter and receiver generator against each other by yielding them
together, as follows::

   def test():
       tx = Signal(1)
       rx = tx
       rxData = intbv(0)
       for val in testvals:
           txData = intbv(val)
           yield rs232_rx(rx, rxData), rs232_tx(tx, txData)

Both forked generators will run concurrently, and the original generator will
resume as soon as one of them finishes (which will be the transmitter in this
case).  The simulation output shows how the UART procedures run in lockstep::

   -- Transmitting 0xc5 --
   TX: start bit
   RX: start bit
   TX: 1
   RX: 1
   TX: 0
   RX: 0
   TX: 1
   RX: 1
   TX: 0
   RX: 0
   TX: 0
   RX: 0
   TX: 0
   RX: 0
   TX: 1
   RX: 1
   TX: 1
   RX: 1
   TX: stop bit
   RX: stop bit
   -- Received 0xc5 --
   -- Transmitting 0x3a --
   TX: start bit
   RX: start bit
   TX: 0
   RX: 0
   ...

For completeness, we will verify the timeout behavior with a test bench that
disconnects the ``rx`` from the ``tx`` signal, and we specify a small timeout
for the receive procedure::

   def testTimeout():
       tx = Signal(1)
       rx = Signal(1)
       rxData = intbv(0)
       for val in testvals:
           txData = intbv(val)
           yield rs232_rx(rx, rxData, timeout=4*T_9600-1), rs232_tx(tx, txData)

The simulation now stops with a timeout exception after a few transmit cycles::

   -- Transmitting 0xc5 --
   TX: start bit
   TX: 1
   TX: 0
   TX: 1
   StopSimulation: RX time out error

Recall that the original generator resumes as soon as one of the forked
generators returns. In the previous cases, this is just fine, as the transmitter
and receiver generators run in lockstep. However, it may be desirable to resume
the caller only when *all* of the forked generators have finished. For example,
suppose that we want to characterize the robustness of the transmitter and
receiver design to bit duration differences. We can adapt our test bench as
follows, to run the transmitter at a faster rate::

   T_10200 = int(1e9 / 10200)

   def testNoJoin():
       tx = Signal(1)
       rx = tx
       rxData = intbv(0)
       for val in testvals:
           txData = intbv(val)
           yield rs232_rx(rx, rxData), rs232_tx(tx, txData, duration=T_10200)

Simulating this shows how the transmission of the new byte starts before the
previous one is received, potentially creating additional transmission errors::

   -- Transmitting 0xc5 --
   TX: start bit
   RX: start bit
   ...
   TX: 1
   RX: 1
   TX: 1
   TX: stop bit
   RX: 1
   -- Transmitting 0x3a --
   TX: start bit
   RX: stop bit
   -- Received 0xc5 --
   RX: start bit
   TX: 0

It is more likely that we want to characterize the design on a byte by byte
basis, and align the two generators before transmitting each byte. In MyHDL,
this is done with the :func:`join` function. By joining clauses together in a
``yield`` statement, we create a new clause that triggers only when all of its
clause arguments have triggered. For example, we can adapt the test bench as
follows::

   def testJoin():
       tx = Signal(1)
       rx = tx
       rxData = intbv(0)
       for val in testvals:
           txData = intbv(val)
           yield join(rs232_rx(rx, rxData), rs232_tx(tx, txData, duration=T_10200))

Now, transmission of a new byte only starts when the previous one is received::

   -- Transmitting 0xc5 --
   TX: start bit
   RX: start bit
   ...
   TX: 1
   RX: 1
   TX: 1
   TX: stop bit
   RX: 1
   RX: stop bit
   -- Received 0xc5 --
   -- Transmitting 0x3a --
   TX: start bit
   RX: start bit
   TX: 0
   RX: 0


.. _model-mem:

Modeling memories with built-in types
-------------------------------------

.. index:: single: modeling; memories

Python has powerful built-in data types that can be useful to model hardware
memories. This can be merely a matter of putting an interface around some data
type operations.

For example, a :dfn:`dictionary` comes in handy to model sparse memory
structures. (In other languages, this data type is called  :dfn:`associative
array`, or :dfn:`hash table`.) A sparse memory is one in which only a small part
of the addresses is used in a particular application or simulation. Instead of
statically allocating the full address space, which can be large, it is better
to dynamically allocate the needed storage space. This is exactly what a
dictionary provides. The following is an example of a sparse memory model::

   def sparseMemory(dout, din, addr, we, en, clk):

       """ Sparse memory model based on a dictionary.

       Ports:
       dout -- data out
       din -- data in
       addr -- address bus
       we -- write enable: write if 1, read otherwise
       en -- interface enable: enabled if 1
       clk -- clock input

       """

       memory = {}

       @always(clk.posedge)
       def access():
           if en:
               if we:
                   memory[addr.val] = din.val
               else:
                   dout.next = memory[addr.val]

       return access

Note how we use the ``val`` attribute of the ``din`` signal, as we don't want to
store the signal object itself, but its current value. Similarly, we use the
``val`` attribute of the ``addr`` signal as the dictionary key.

In many cases, MyHDL code uses a signal's current value automatically when there
is no ambiguity: for example, when a signal is used in an expression. However,
in other cases such as in this example you have to refer to the value
explicitly: for example, when the Signal is used as an index, or when it is not
used in an expression.  One option is to use the ``val`` attribute, as in this
example.  Another possibility is to use the ``int()`` or ``bool()`` functions to
typecast the Signal to an integer or a boolean value. These functions are also
useful with :class:`intbv` objects.

As a second example, we will demonstrate how to use a list to model a
synchronous fifo::

   def fifo(dout, din, re, we, empty, full, clk, maxFilling=sys.maxint):

       """ Synchronous fifo model based on a list.

       Ports:
       dout -- data out
       din -- data in
       re -- read enable
       we -- write enable
       empty -- empty indication flag
       full -- full indication flag
       clk -- clock input

       Optional parameter:
       maxFilling -- maximum fifo filling, "infinite" by default

       """

       memory = []

       @always(clk.posedge)
       def access():
           if we:
               memory.insert(0, din.val)
           if re:
               dout.next = memory.pop()
           filling = len(memory)
           empty.next = (filling == 0)
           full.next = (filling == maxFilling)

       return access

Again, the model is merely a MyHDL interface around some operations on a list:
:func:`insert` to insert entries, :func:`pop` to retrieve them, and :func:`len`
to get the size of a Python object.


.. _model-err:

Modeling errors using exceptions
--------------------------------

In the previous section, we used Python data types for modeling. If such a type
is used inappropriately, Python's run time error system will come into play. For
example, if we access an address in the :func:`sparseMemory` model that was not
initialized before, we will get a traceback similar to the following (some lines
omitted for clarity)::

   Traceback (most recent call last):
   ...
     File "sparseMemory.py", line 31, in access
       dout.next = memory[addr.val]
   KeyError: Signal(51)

Similarly, if the ``fifo`` is empty, and we attempt to read from it, we get::

   Traceback (most recent call last):
   ...
     File "fifo.py", line 34, in fifo
       dout.next = memory.pop()
   IndexError: pop from empty list

Instead of these low level errors, it may be preferable to define errors at the
functional level. In Python, this is typically done by defining a custom
``Error`` exception, by subclassing the standard ``Exception`` class. This
exception is then raised explicitly when an error condition occurs.

For example, we can change the :func:`sparseMemory` function as follows (with
the doc string is omitted for brevity)::

   class Error(Exception):
       pass

   def sparseMemory2(dout, din, addr, we, en, clk):

       memory = {}

       @always(clk.posedge)
       def access():
           if en:
               if we:
                   memory[addr.val] = din.val
               else:
                   try:
                       dout.next = memory[addr.val]
                   except KeyError:
                       raise Error, "Uninitialized address %s" % hex(addr)

       return access


This works by catching the low level data type exception, and raising the custom
exception with an appropriate error message instead.  If the
:func:`sparseMemory` function is defined in a module with the same name, an
access error is now reported as follows::

   Traceback (most recent call last):
   ...
     File "sparseMemory.py", line 61, in access
       raise Error, "Uninitialized address %s" % hex(addr)
   Error: Uninitialized address 0x33


Likewise, the :func:`fifo` function can be adapted as follows, to report
underflow and overflow errors::

   class Error(Exception):
       pass


   def fifo2(dout, din, re, we, empty, full, clk, maxFilling=sys.maxint):

       memory = []

       @always(clk.posedge)
       def access():
           if we:
               memory.insert(0, din.val)
           if re:
               try:
                   dout.next = memory.pop()
               except IndexError:
                   raise Error, "Underflow -- Read from empty fifo"
           filling = len(memory)
           empty.next = (filling == 0)
           full.next = (filling == maxFilling)
           if filling > maxFilling:
               raise Error, "Overflow -- Max filling %s exceeded" % maxFilling

       return access

In this case, the underflow error is detected as before, by catching a low level
exception on the list data type. On the other hand, the overflow error is
detected by a regular check on the length of the list.


.. _model-obj:

Object oriented modeling
------------------------

.. index:: single: modeling; object oriented

The models in the previous sections used high-level built-in data types
internally. However, they had a conventional RTL-style interface.  Communication
with such a module is done through signals that are attached to it during
instantiation.

A more advanced approach is to model hardware blocks as objects. Communication
with objects is done through method calls. A method encapsulates all details of
a certain task performed by the object. As an object has a method interface
instead of an RTL-style hardware interface, this is a much  higher level
approach.

As an example, we will design a synchronized queue object.  Such an object can
be filled by producer, and independently read by a consumer. When the queue is
empty, the consumer should wait until an item is available. The queue can be
modeled as an object with a :meth:`put(item)` and a :meth:`get` method, as
follows::

   from myhdl import *

   def trigger(event):
       event.next = not event

   class queue:
       def __init__(self):
          self.l = []
          self.sync = Signal(0)
          self.item = None
       def put(self,item):
          # non time-consuming method
          self.l.append(item)
          trigger(self.sync)
       def get(self):
          # time-consuming method
          if not self.l:
             yield self.sync
          self.item = self.l.pop(0)

The :class:`queue` object constructor initializes an internal list to hold
items, and a *sync* signal to synchronize the operation between the methods.
Whenever :meth:`put` puts an item in the queue, the signal is triggered.  When
the :meth:`get` method sees that the list is empty, it waits on the trigger
first. :meth:`get` is a generator method because  it may consume time. As the
``yield`` statement is used in MyHDL\ for timing control, the method cannot
"yield" the item. Instead, it makes it available in the *item* instance
variable.

To test the queue operation, we will model a producer and a consumer in the test
bench.  As a waiting consumer should not block a whole system, it should run in
a concurrent "thread". As always in MyHDL, concurrency is modeled by Python
generators. Producer and consumer will thus run independently, and we will
monitor their operation through some print statements::

   q = queue()

   def Producer(q):
       yield delay(120)
       for i in range(5):
           print "%s: PUT item %s" % (now(), i)
           q.put(i)
           yield delay(max(5, 45 - 10*i))

   def Consumer(q):
       yield delay(100)
       while 1:
           print "%s: TRY to get item" % now()
           yield q.get()
           print "%s: GOT item %s" % (now(), q.item)
           yield delay(30)

   def main():
       P = Producer(q)
       C = Consumer(q)
       return P, C 

   sim = Simulation(main())
   sim.run()

Note that the generator method :meth:`get` is called in a ``yield`` statement in
the :func:`Consumer` function. The new generator will take over from
:func:`Consumer`, until it is done. Running this test bench produces the
following output::

   % python queue.py
   100: TRY to get item
   120: PUT item 0
   120: GOT item 0
   150: TRY to get item
   165: PUT item 1
   165: GOT item 1
   195: TRY to get item
   200: PUT item 2
   200: GOT item 2
   225: PUT item 3
   230: TRY to get item
   230: GOT item 3
   240: PUT item 4
   260: TRY to get item
   260: GOT item 4
   290: TRY to get item
   StopSimulation: No more events

.. rubric:: Footnotes

.. [#] The name :func:`always_comb` refers to a construct with similar semantics in
   SystemVerilog.

.. [#] It also possible to have a reproducible random output, by explicitly providing a
   seed value. See the documentation of the ``random`` module.

