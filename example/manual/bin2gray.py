from myhdl import block, always_comb

@block
def bin2gray(B, G):
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    """

    @always_comb
    def logic():
        G.next = (B>>1) ^ B

    return logic
