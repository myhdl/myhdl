'''
Created on 4 feb. 2024

@author: josy
'''

from myhdl import (block, Signal, intbv, delay, always_comb, always_seq, enum,
                   always, instance, StopSimulation, ResetSignal, Constant,
                   conversion)
from myhdl import ConversionError
from myhdl.conversion._misc import _error


@block
def listofenums(Clk, Reset, Start, Progress, Ended):
    listofenums_states = enum('IDLE', 'Doing_Nothing', 'Procrastinating', 'Getting_Ready', 'Executing', encoding='one_hot')

    smn, smp = [Signal(listofenums_states.IDLE) for __ in range(2)]
    stack = [Constant(listofenums_states.IDLE),
             Constant(listofenums_states.Doing_Nothing),
             Constant(listofenums_states.Procrastinating),
             Constant(listofenums_states.Getting_Ready),
             Constant(listofenums_states.Executing)]
    NBR_STATES = len(stack)
    stateindex = Signal(intbv(0)[3:])

    @always_comb
    def smcomb():
        Ended.next = 0

        # if smp == listofenums_states.IDLE:
        if Start:
                smn.next = stack[1]
            # else:
            #     smn.next = smp
        elif Progress:
            if stateindex < NBR_STATES - 1:
                smn.next = stack[stateindex + 1]
            else:
                smn.next = smp
        else:
            smn.next = smp

        '''
            note that if we exchange the two following lines
            we get a failing conversion to VHDL (only; Verilog is fine ...) 
        '''
        if smp == listofenums_states.Executing:
        # if stateindex == NBR_STATES - 1:
            Ended.next = 1

        # smn.next = smp
        # if smp == listofenums_states.IDLE:
        #     if Start:
        #         smn.next = listofenums_states.Doing_Nothing
        #
        # elif smp == listofenums_states.Doing_Nothing:
        #     if Start:
        #         smn.next = listofenums_states.Procrastinating
        #
        # elif smp == listofenums_states.Procrastinating:
        #     if Start:
        #         smn.next = listofenums_states.Getting_Ready
        #
        # elif smp == listofenums_states.Getting_Ready:
        #     if Start:
        #         smn.next = listofenums_states.Executing
        #
        # elif smp == listofenums_states.Executing:
        #     smn.next = listofenums_states.Executing
        #     Ended.next = 1
        #
        # else:
        #     smn.next = listofenums_states.IDLE

    @always_seq(Clk.posedge, reset=Reset)
    def smsync():
        smp.next = smn
        if Start or Progress:
            if stateindex < NBR_STATES - 1:
                stateindex.next = stateindex + 1

    return smcomb, smsync


def test_listofenums():
    Clk, Start, Progress, Ended = [Signal(bool(0)) for __ in range(4)]
    Reset = ResetSignal(0, 1, False)
    assert listofenums(Clk, Reset, Start, Progress, Ended).analyze_convert() == 0


if __name__ == '__main__':
    Clk, Start, Progress, Ended = [Signal(bool(0)) for __ in range(4)]
    Reset = ResetSignal(0, 1, False)
    dfc = listofenums(Clk, Reset, Start, Progress, Ended)
    dfc.convert(hdl='Verilog', initial_values=True)
    dfc.convert(hdl='VHDL', initial_values=True)
