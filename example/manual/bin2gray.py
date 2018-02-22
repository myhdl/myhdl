from myhdl import block, always_comb

@block
def bin2gray(B, G):
    """ Gray encoder.

    B -- binary input 
    G -- Gray encoded output
    """

    @always_comb
    def logic():
        G.next = (B>>1) ^ B

    return logic

