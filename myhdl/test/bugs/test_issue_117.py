import myhdl
from myhdl import *
#from myhdl.conversion import analyze

@block
def issue_117(clk, sdi, pdo, sel, const=False):
     assert isinstance(const, (bool, intbv))
     delay_reg = Signal(intbv(0)[8:])
     rlen = len(pdo)
     plen = 1 if isinstance(const, bool) else len(const)
     @always(clk.posedge)
     def rtl():
          if sel == 0:
               delay_reg.next = concat(const, delay_reg[rlen-plen-1:1], sdi)
          elif sel == 1:
               delay_reg.next = concat(delay_reg[rlen-1:plen+1], const, sdi)
          elif sel == 2:
               delay_reg.next = concat(delay_reg[rlen-1:plen+1], sdi, const)
               pdo.next = delay_reg
     return rtl

def test_issue_117_1():
     clk, sdi = [Signal(bool(0)) for _ in range(2)]
     pdo = Signal(intbv(0)[8:])
     sel = Signal(intbv(0, min=0, max=3))
     toVHDL.name = toVerilog.name = 'issue_117_1'
     assert issue_117(clk, sdi, pdo, sel, const=bool(0)).analyze_convert() == 0


def test_issue_117_2():
     clk, sdi = [Signal(bool(0)) for _ in range(2)]
     pdo = Signal(intbv(0)[8:])
     sel = Signal(intbv(0, min=0, max=3))
     toVHDL.name = toVerilog.name = 'issue_117_2'
     assert issue_117(clk, sdi, pdo, sel, const=False).analyze_convert() == 0


def test_issue_117_3():
     clk, sdi = [Signal(bool(0)) for _ in range(2)]
     pdo = Signal(intbv(0)[8:])
     sel = Signal(intbv(0, min=0, max=3))
     toVHDL.name = toVerilog.name = 'issue_117_3'
     assert issue_117(clk, sdi, pdo, sel, const=intbv(0)[1:]).analyze_convert() == 0


if __name__ == '__main__':
    analyze.simulator='vlog'
    test_issue_117_1()
     

