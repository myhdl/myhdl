from myhdl import block, Signal, intbv, delay, instance, bin

from bin2gray import bin2gray

@block
def testbench(width):

    B = Signal(intbv(0)[width:])
    G = Signal(intbv(0)[width:])

    dut = bin2gray(B, G)
    dut.config_sim(trace=True)

    @instance
    def stimulus():
        for i in range(2**width):
            B.next = intbv(i)
            yield delay(10)
            print("B: " + bin(B, width) + "| G: " + bin(G, width))

    return dut, stimulus

def main():
    tb = testbench(width=3)
    # tb.config_sim(trace=True)
    tb.run_sim()

if __name__ == '__main__':
    main()
