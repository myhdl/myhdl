from __future__ import absolute_import
from myhdl import *

#t_state = enum('WAIT_POSEDGE', 'WAIT_NEGEDGE', encoding='one_hot')
t_state = enum('WAIT_POSEDGE', 'WAIT_NEGEDGE')

def pcie_legacyint_next_state_logic(state_i, next_state_o, next_state_en_o, interrupt_pending_i, interrupt_assert_o):
        @always_comb
        def sm_output(): # state machine
                if state_i==t_state.WAIT_POSEDGE:
                        interrupt_assert_o.next=0
                        next_state_en_o   .next=interrupt_pending_i
                        next_state_o      .next=t_state.WAIT_NEGEDGE
                elif state_i==t_state.WAIT_NEGEDGE:
                        interrupt_assert_o.next=1
                        next_state_en_o   .next=not interrupt_pending_i
                        next_state_o      .next=t_state.WAIT_POSEDGE
                else:
                        interrupt_assert_o.next=0
                        next_state_en_o   .next=1
                        next_state_o      .next=t_state.WAIT_POSEDGE
        return sm_output 

state         = Signal(t_state.WAIT_POSEDGE)
next_state    = Signal(t_state.WAIT_POSEDGE)
next_state_en = Signal(bool(0)) # Enable transition to next state
interrupt_pending = Signal(bool(0))
interrupt_assert  = Signal(bool(0))

def test_bug_enum_toVHDL():
    toVHDL(pcie_legacyint_next_state_logic, state, next_state, next_state_en, interrupt_pending, interrupt_assert)

