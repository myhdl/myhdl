from myhdl import block, always_comb


@block
def bin2gray(B, G):
    # INCORRECT IMPLEMENTATION
    """ Gray encoder.

    B -- binary input 
    G -- Gray encoded output
    """

    @always_comb
    def comb():
        G.next = B[0]

    return comb
