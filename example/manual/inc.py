from myhdl import block, always_seq

@block
def inc(count, enable, clock, reset):
    """ Incrementer with enable.

    count -- output
    enable -- control input, increment when 1
    clock -- clock input
    reset -- asynchronous reset input
    """
    
    @always_seq(clock.posedge, reset=reset)
    def seq():
        if enable:
            count.next = count + 1

    return seq
