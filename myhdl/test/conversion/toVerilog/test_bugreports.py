import myhdl
from myhdl import *

from .util import verilogCompile

#############################
# bug report (Tom Dillon)
# conflicts in reg/wire names
#############################

width = 8

@block
def add(x,a,b) :
    def logic() :
        x.next = a + b
    L0 = always_comb(logic)
    return L0

@block
def add3(x,a,b,c) :
    x0 = Signal(intbv(0,min=-2**(width-1),max=2**(width-1)))
    A0 = add(x0,a,b)
    A1 = add(x,x0,c)

    return instances()

@block
def DUT_Verilog_001(x,a,b,c,d,e) :
    x0 = Signal(intbv(0,min=-2**(width-1),max=2**(width-1)))

    A0 = add3(x0,a,b,c)
    A1 = add3(x,x0,d,e)

    return instances()


def test_bugreports_001():
    x,a,b,c,d,e = [Signal(intbv(0,min=-2**(width-1),max=2**(width-1))) for i in range(6)]

    DUT_Verilog_001(x,a,b,c,d,e).convert(hdl='Verilog')
    #verilogCompile(TestModule.__name__)

#test()


##############################
# Bug report (Tom Dillon)
# Conflicts in reg/wire names
###############################

@block
def add(x,a,b) :
    def logic() :
        x.next = a + b
    L0 = always_comb(logic)
    return L0

@block
def add4(x,a,b,c,d) :
    xL = [Signal(intbv(0,min=-2**(width+2),max=2**(width+2))) for i in range(2)]

    #xl0 = Signal(intbv(0,min=-2**(width+2),max=2**(width+2)))
    #xl1 = Signal(intbv(0,min=-2**(width+2),max=2**(width+2)))

    A0 = add(xL[0],a,b)
    A1 = add(xL[1],xL[0],c)
    A2 = add(x, xL[1],d)

    return instances()

@block
def DUT_Verilog_002(x,a,b,c,d,e):
    x0 = Signal(intbv(0,min=-2**(width+2),max=2**(width+2)))

    A0 = add4(x0,a,b,c,d)
    A1 = add4(x,x0,e,a,b)

    return instances()

def test_bugreports_002():
    width = 8

    x,a,b,c,d,e = [Signal(intbv(0,min=-2**(width-1),max=2**(width-1))) for i in range(6)]

    DUT_Verilog_002(x,a,b,c,d,e).convert(hdl='Verilog')
    verilogCompile(DUT_Verilog_002.__name__)

#test()

###################################
# Bug report (George Pantazopoulos)
# case variable name in embedded FSM
####################################

from .test_fsm import FramerCtrl

@block
def mid(SOF, clk, reset_n):
    t_State = enum('SEARCH', 'CONFIRM', 'SYNC')
    syncFlag = Signal(bool(0))
    state = Signal(t_State.SEARCH)
    
    fsm_1 = FramerCtrl(SOF, state, syncFlag, clk, reset_n, t_State)

    return fsm_1


@block
def DUT_Verilog_003(SOF, clk, reset_n):
    mid_1 = mid(SOF, clk, reset_n)
    return mid_1


def test_bugreports_003():
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    SOF = Signal(bool(0))
   
    DUT_Verilog_003(SOF, clk, reset_n).convert()
    verilogCompile(DUT_Verilog_003.__name__)

#test()

