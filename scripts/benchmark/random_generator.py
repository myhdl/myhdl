from __future__ import absolute_import
import myhdl
from myhdl import *

def random_generator(random_word, enable, clock, reset):

    W = len(random_word)

    @instance
    def logic():
        lfsr = modbv(0)[64:]
        word =  modbv(0)[W:]
        while True:
            yield clock.posedge, reset.posedge
            if reset == 1:
                random_word.next = 0
                lfsr[:] = 1
            else:
                if enable:
                    for i in range(W):
                        word[i] = lfsr[63]
                        tmp0 = lfsr[63] ^ lfsr[62] ^ lfsr[60] ^ lfsr[59]
                        lfsr <<= 1
                        lfsr[0] = tmp0
                    random_word.next = word

    return logic



                    
# def random_generator(random_word, enable, clock, reset):

#     W = len(random_word)

#     @instance
#     def logic():
#         lfsr = intbv(0)[64:]
#         word =  intbv(0)[W:]
#         while True:
#             yield clock.posedge, reset.posedge
#             if reset == 1:
#                 random_word.next = 0
#                 lfsr[:] = 0
#                 lfsr[63] = 1
#             else:
#                 if enable:
#                     for i in range(W):
#                         word[i] = lfsr[0]
#                         tmp63 = lfsr[0] ^ lfsr[1] ^ lfsr[3] ^ lfsr[4]
#                         lfsr >>= 1
#                         lfsr[63] = tmp63
#                     random_word.next = word

#     return logic



                    
