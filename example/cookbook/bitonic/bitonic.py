from myhdl import *
from myhdl.conversion import analyze

DESCENDING, ASCENDING = False, True

def compare(a1, a2, z1, z2, dir):
    
    @always_comb
    def logic():
        z1.next = a1
        z2.next = a2
        if dir == (a1 > a2):
            z1.next = a2
            z2.next = a1
            
    return logic


def feedthru(a, z):
    
    @always_comb
    def logic():
        z.next = a
        
    return logic


def bitonicMerge(a, z, dir):
    
    n = len(a)
    k = n//2
    w = len(a[0])
    
    if n > 1:
        t = [Signal(intbv(0)[w:]) for i in range(n)]
        comp = [compare(a[i], a[i+k], t[i], t[i+k], dir) for i in range(k)]
        loMerge = bitonicMerge(t[:k], z[:k], dir)
        hiMerge = bitonicMerge(t[k:], z[k:], dir)
        return comp, loMerge, hiMerge
    else:
        feed = feedthru(a[0], z[0])
        return feed


def bitonicSort(a, z, dir):
    
    n = len(a)
    k = n//2
    w = len(a[0])
    
    if n > 1:
        t = [Signal(intbv(0)[w:]) for i in range(n)]
        loSort = bitonicSort(a[:k], t[:k], ASCENDING)
        hiSort = bitonicSort(a[k:], t[k:], DESCENDING)
        merge = bitonicMerge(t, z, dir)
        return loSort, hiSort, merge
    else:
        feed = feedthru(a[0], z[0])
        return feed
            

def Array8Sorter(a0, a1, a2, a3, a4, a5, a6, a7,
                 z0, z1, z2, z3, z4, z5, z6, z7):

    a = [a0, a1, a2, a3, a4, a5, a6, a7]
    z = [z0, z1, z2, z3, z4, z5, z6, z7]
    sort = bitonicSort(a, z, ASCENDING)
    return sort


def Array8Sorter_v(a0, a1, a2, a3, a4, a5, a6, a7,
                   z0, z1, z2, z3, z4, z5, z6, z7):
    
    toVerilog(Array8Sorter, a0, a1, a2, a3, a4, a5, a6, a7,
                            z0, z1, z2, z3, z4, z5, z6, z7)
    analyze(Array8Sorter, a0, a1, a2, a3, a4, a5, a6, a7,
                         z0, z1, z2, z3, z4, z5, z6, z7)
    cmd = "cver -q +loadvpi=../../../cosimulation/cver/myhdl_vpi:vpi_compat_bootstrap " + \
          "Array8Sorter.v tb_Array8Sorter.v"
    return Cosimulation(cmd, **locals())


