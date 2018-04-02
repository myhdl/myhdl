.. currentmodule:: myhdl

.. _model-hl:

*******************
High level modeling
*******************

Introduction
============

.. index:: single: modeling; high level

To write synthesizable models in MyHDL, you should stick to
the RTL templates shown in :ref:`model-rtl`. However,
modeling in MyHDL is much more powerful than that.
Conceptually, MyHDL is a library for general event-driven
modeling and simulation of hardware systems.

There are many reasons why it can be useful to model at a
higher abstraction level than RTL. For example, you can
use MyHDL to verify architectural features, such as system
throughput, latency and buffer sizes. You can also write
high level models for specialized technology-dependent cores
that are not going through synthesis. Last but not least,
you can use MyHDL to write test benches that verify a system
model or a synthesizable description.

This chapter explores some of the options for high level
modeling with MyHDL.


.. _model-bfm:

Modeling with bus-functional procedures
=======================================

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
=====================================

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
in other cases, such as in this example, you have to refer to the value
explicitly: for example, when the Signal is used as a dictionary key, or when it is not
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
================================

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
========================

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
``yield`` statement is used in MyHDL for timing control, the method cannot
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


