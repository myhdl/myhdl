import subprocess

import myhdl
from myhdl import *
from myhdl.conversion import analyze

DESCENDING, ASCENDING = False, True

@block
def comp(a1, a2, z1, z2, dir):

    @always_comb
    def logic():
        z1.next = a1
        z2.next = a2
        if dir == (a1 > a2):
            z1.next = a2
            z2.next = a1

    return logic


@block
def feedthru(a, z):

    @always_comb
    def logic():
        z.next = a

    return logic


@block
def bitonicMerge(a, z, dir):

    n = len(a)
    k = n//2
    w = len(a[0])

    if n > 1:
        t = [Signal(intbv(0)[w:]) for i in range(n)]
        comps = [comp(a[i], a[i+k], t[i], t[i+k], dir) for i in range(k)]
        lomerge = bitonicMerge(t[:k], z[:k], dir)
        himerge = bitonicMerge(t[k:], z[k:], dir)
        lomerge.name = "lomerge"
        himerge.name = "hiMerge"
        return comps, lomerge, himerge
    else:
        return feedthru(a[0], z[0])


@block
def bitonicSort(a, z, dir):

    n = len(a)
    k = n//2
    w = len(a[0])

    if n > 1:
        t = [Signal(intbv(0)[w:]) for i in range(n)]
        losort = bitonicSort(a[:k], t[:k], ASCENDING)
        hisort = bitonicSort(a[k:], t[k:], DESCENDING)
        merge = bitonicMerge(t, z, dir)
        losort.name = "losort"
        hisort.name = "hisort"
        merge.name = "merge"
        return losort, hisort, merge
    else:
        return feedthru(a[0], z[0])

@block
def Array8Sorter(a0, a1, a2, a3, a4, a5, a6, a7,
                 z0, z1, z2, z3, z4, z5, z6, z7):

    a = [a0, a1, a2, a3, a4, a5, a6, a7]
    z = [z0, z1, z2, z3, z4, z5, z6, z7]
    sort = bitonicSort(a, z, ASCENDING)
    sort.name = "sort"
    return sort


def Array8Sorter_v(a0, a1, a2, a3, a4, a5, a6, a7,
                   z0, z1, z2, z3, z4, z5, z6, z7):

    analyze.simulator = 'iverilog'
    toVerilog(Array8Sorter(a0, a1, a2, a3, a4, a5, a6, a7,
                           z0, z1, z2, z3, z4, z5, z6, z7))
    analyze(Array8Sorter(a0, a1, a2, a3, a4, a5, a6, a7,
                         z0, z1, z2, z3, z4, z5, z6, z7))
    # cmd = "cver -q +loadvpi=../../../cosimulation/cver/myhdl_vpi:vpi_compat_bootstrap " + \
    #      "Array8Sorter.v tb_Array8Sorter.v"
    subprocess.call("iverilog -o Array8Sorter.o Array8Sorter.v tb_Array8Sorter.v", shell=True)
    cmd = "vvp -m ../../../cosimulation/icarus/myhdl.vpi Array8Sorter.o"
    return Cosimulation(cmd, **locals())
