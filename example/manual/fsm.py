from __future__ import generators

from myhdl import *

# SEARCH, CONFIRM, SYNC = range(3)]
ACTIVE_LOW = 0
FRAME_SIZE = 8

FramerState = enum('SEARCH', 'CONFIRM', 'SYNC')

def FramerCtrl(SOF, state, syncFlag, clk, reset_n):
    
    """ Framing control FSM.

    SOF -- start-of-frame output bit
    state -- FramerState output
    syncFlag -- sync pattern found indication input
    clk -- clock input
    reset_n -- active low reset
    
    """
    
    index = Signal(0) # position in frame

    def FSM():
        while 1:
            yield posedge(clk), negedge(reset_n)
            
            if reset_n == ACTIVE_LOW:
                SOF.next = 0
                index.next = 0
                state.next = FramerState.SEARCH
            else:
                index.next = (index + 1) % FRAME_SIZE
                SOF.next = 0
                if state == FramerState.SEARCH:
                    index.next = 1
                    if syncFlag:
                        state.next = FramerState.CONFIRM
                elif state == FramerState.CONFIRM:
                    if index == 0:
                        if syncFlag:
                            state.next = FramerState.SYNC
                        else:
                            state.next = FramerState.SEARCH
                elif state == FramerState.SYNC:
                    if index == 0:
                        if not syncFlag:
                            state.next = FramerState.SEARCH
                    SOF.next = (index == FRAME_SIZE-1)
                else:
                    raise ValueError

    return FSM()


def testbench():

    SOF, syncFlag, clk, reset_n = [Signal(bool(0)) for i in range(4)]
    state = Signal(FramerState.SEARCH)
            
    framectrl = FramerCtrl(SOF, state, syncFlag, clk, reset_n)

    def clkgen():
        while 1:
            yield delay(10)
            clk.next = not clk

    def stimulus():
        reset_n.next = 0
        yield posedge(clk)
        reset_n.next = 1
        yield posedge(clk)
        yield posedge(clk)
        for n in (12, 8, 8, 4):
            syncFlag.next = 1
            yield posedge(clk)
            syncFlag.next = 0
            for i in range(n-1):
                yield posedge(clk)
        raise StopSimulation
        
    return framectrl, clkgen(), stimulus()

tb_fsm = traceSignals(testbench)

sim = Simulation(tb_fsm)
sim.run()
