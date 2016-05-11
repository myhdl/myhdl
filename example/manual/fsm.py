from myhdl import block, always_seq, Signal, intbv, enum

ACTIVE_LOW = 0
FRAME_SIZE = 8
t_state = enum('SEARCH', 'CONFIRM', 'SYNC')

@block
def framer_ctrl(sof, state, sync_flag, clk, reset_n):

    """ Framing control FSM.

    sof -- start-of-frame output bit
    state -- FramerState output
    sync_flag -- sync pattern found indication input
    clk -- clock input
    reset_n -- active low reset

    """

    index = Signal(intbv(0, min=0, max=FRAME_SIZE)) # position in frame

    @always_seq(clk.posedge, reset=reset_n)
    def FSM():
        if reset_n == ACTIVE_LOW:
            sof.next = 0
            index.next = 0
            state.next = t_state.SEARCH

        else:
            index.next = (index + 1) % FRAME_SIZE
            sof.next = 0

            if state == t_state.SEARCH:
                index.next = 1
                if sync_flag:
                    state.next = t_state.CONFIRM

            elif state == t_state.CONFIRM:
                if index == 0:
                    if sync_flag:
                        state.next = t_state.SYNC
                    else:
                        state.next = t_state.SEARCH

            elif state == t_state.SYNC:
                if index == 0:
                    if not sync_flag:
                        state.next = t_state.SEARCH
                sof.next = (index == FRAME_SIZE-1)

            else:
                raise ValueError("Undefined state")

    return FSM
