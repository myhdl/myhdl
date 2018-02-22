from myhdl import always_comb

def bin2gray(B, G, width):
    """ Gray encoder.

    B -- input intbv signal, binary encoded
    G -- output intbv signal, gray encoded
    width -- bit width
    """

    @always_comb
    def logic():
        for i in range(width):
            G.next[i] = B[i+1] ^ B[i]

    return logic
