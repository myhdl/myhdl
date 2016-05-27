import myhdl
from myhdl import block, always, instance, Signal, ResetSignal, delay, StopSimulation
from fsm import framer_ctrl, t_state

ACTIVE_LOW = 0

@block
def testbench():

    sof = Signal(bool(0))
    sync_flag = Signal(bool(0))
    clk = Signal(bool(0))
    reset_n = ResetSignal(1, active=ACTIVE_LOW, async=True)
    state = Signal(t_state.SEARCH)

    frame_ctrl_0 = framer_ctrl(sof, state, sync_flag, clk, reset_n)

    @always(delay(10))
    def clkgen():
        clk.next = not clk

    @instance
    def stimulus():
        for i in range(3):
            yield clk.negedge
        for n in (12, 8, 8, 4):
            sync_flag.next = 1
            yield clk.negedge
            sync_flag.next = 0
            for i in range(n-1):
                yield clk.negedge
        raise StopSimulation()

    return frame_ctrl_0, clkgen, stimulus

tb = testbench()
tb.config_sim(trace=True)
tb.run_sim()
