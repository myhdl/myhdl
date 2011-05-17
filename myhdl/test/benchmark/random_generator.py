from myhdl import *

def random_generator(random_word, enable, clock, reset):

    W = len(random_word)

    @instance
    def logic():
        lfsr = intbv(0)[64:]
        while True:
            yield clock.posedge, reset.posedge
            if reset == 1:
                random_word.next = 0
                lfsr[:] = 1
            else:
                if enable:
                    for i in range(W):
                        random_word.next[i] = lfsr[63]
                        lfsr[64:1] = lfsr[63:0]
                        lfsr[0] = lfsr[63] ^ lfsr[62] ^ lfsr[60] ^ lfsr[59]

    return logic



                    
