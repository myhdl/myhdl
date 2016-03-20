import myhdl
from myhdl import *

from random import randrange

def arbiter(grant_vector, request_vector):
    
    @always_comb
    def logic():
        grant_vector.next = 0
        for i in range(len(request_vector)):
            if request_vector[i] == 1:
                grant_vector.next[i] = 1
                break

    return logic


def check():

    M = 8

    request_list = [Signal(bool()) for i in range(M)]

    request_vector = ConcatSignal(*reversed(request_list))

    grant_vector = Signal(intbv(0)[M:])

    grant_list = [grant_vector(i) for i in range(M)]

    arb = arbiter(grant_vector, request_vector)

    @instance
    def stimulus():
        for i in range(100):
            for j in range(M):
                request_list[j].next = randrange(2)
            yield delay(10)
            if 1 in request_list:
                assert grant_list.index(1) == request_list.index(1)
                assert grant_list.count(0) == M-1
                #print bin(grant_vector, 8), bin(request_vector, 8)
        raise StopSimulation()

    return arb, stimulus
        
        

sim = Simulation(check())
sim.run()

                 




    
