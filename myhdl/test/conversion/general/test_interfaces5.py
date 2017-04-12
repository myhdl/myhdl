"""
This set of tests checks the conversion of nested top level interfaces
"""

from __future__ import absolute_import, print_function

import sys

from myhdl import block, Signal, ResetSignal, intbv, always_seq, conversion


class NestedInterface(object):
    ''' interface to describe what is actually transferred '''
    def __init__(self):
        self.error = Signal(bool(0))
        self.user = Signal(bool(0))
        self.data = Signal(intbv(0)[8:])


class TopInterface(object):
    ''' the interface to transfer data between a Sink and A Source '''
    def __init__(self):
        self.valid = Signal(bool(0))
        self.ready = Signal(bool(0))
        self.payload = NestedInterface()


@block
def five(clock, reset, sink, source):
    ''' a minimal exercise '''
    @always_seq(clock.posedge, reset=reset)
    def comb():
        ''' 'connect' the signals '''
        # cross-connect the handshake signals
        sink.ready.next = source.ready
        source.valid.next = sink.valid
        # we can't assign interfaces, so we have to do it 'manually'
        # for each member in the nested interface
        source.payload.data.next = sink.payload.data
        source.payload.error.next = sink.payload.error
        source.payload.user.next = sink.payload.user

    return comb


def test_five_analyze():
    ''' analyse the conversion output '''
    clock = Signal(bool(0))
    reset = ResetSignal(0, active=1, async=False)
    sink = TopInterface()
    source = TopInterface()

    conversion.analyze(five(clock, reset, sink, source))


if __name__ == '__main__':
    print('Using: {} as simulator'.format(sys.argv[1]))
    conversion.analyze.simulator = sys.argv[1]
    print("*** analyze example module conversion ")
    test_five_analyze()

