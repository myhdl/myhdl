import os
path = os.path
import unittest
from unittest import TestCase

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
    
    index = Signal(intbv(0)[8:]) # position in frame

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

    FSM_1 = FSM()
    return FSM_1

objfile = "framerctrl.o"
analyze_cmd = "iverilog -o %s framerctrl.v tb_framerctrl.v" % objfile
simulate_cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi %s" % objfile


def FramerCtrl_v(SOF, state, syncFlag, clk, reset_n):
    if path.exists(objfile):
        os.remove(objfile)
    os.system(analyze_cmd)
    return Cosimulation(simulate_cmd, **locals())
    

class FramerCtrlTest(TestCase):
    
    def bench(self):

        SOF = Signal(bool(0))
        SOF_v = Signal(bool(0))
        syncFlag = Signal(bool(0))
        clk = Signal(bool(0))
        reset_n = Signal(bool(1))
        state = Signal(t_State.SEARCH)
        state_v = Signal(intbv(0)[2:])

        framerctrl = toVerilog(FramerCtrl, SOF, state, syncFlag, clk, reset_n)
        framerctrl_v = FramerCtrl_v(SOF_v, state_v, syncFlag, clk, reset_n)

        def clkgen():
            reset_n.next = 1
            yield delay(10)
            reset_n.next = 0
            yield delay(10)
            reset_n.next = 1
            yield delay(10)
            while 1:
                yield delay(10)
                clk.next = not clk

        def stimulus():
            for i in range(3):
                yield posedge(clk)
            for n in (12, 8, 8, 4, 11, 8, 8, 7, 6, 8, 8):
                syncFlag.next = 1
                yield posedge(clk)
                syncFlag.next = 0
                for i in range(n-1):
                    yield posedge(clk)
            raise StopSimulation

        def check():
            while 1:
                yield negedge(clk)
                self.assertEqual(SOF, SOF_v)
                self.assertEqual(eval(hex(state)), eval(hex(state_v)))
                # print "MyHDL: %s %s" % (SOF, hex(state))
                # print "Verilog: %s %s" % (SOF_v, hex(state_v))

        return framerctrl, framerctrl_v, clkgen(), stimulus(), check()


    def test(self):
        tb_fsm = self.bench()
        sim = Simulation(tb_fsm)
        sim.run()
        

if __name__ == '__main__':
    unittest.main()
