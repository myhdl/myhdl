import myhdl
from myhdl import *

# SEARCH, CONFIRM, SYNC = range(3)
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

    @instance
    def FSM():
        while 1:
            yield posedge(clk), negedge(reset_n)
            
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

    # FSM_1 = FSM()
    return FSM


def testbench():

    SOF = Signal(bool(0))
    syncFlag = Signal(bool(0))
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    state = Signal(t_State.SEARCH)
            
    framectrl = FramerCtrl(SOF, state, syncFlag, clk, reset_n)

    @instance
    def clkgen():
        while 1:
            yield delay(10)
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


def main():
    traceSignals.name = "fsm2"
    tb_fsm = traceSignals(testbench)
    sim = Simulation(tb_fsm)
    sim.run()

if __name__ == '__main__':
    main()
