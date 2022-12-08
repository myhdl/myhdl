from myhdl import *

@block
def chunk_buffer(Clk, Reset, Input, Output):
    OUTPUT_BIT_COUNT = len(Output)
    idx = Signal(modbv(0)[(len(Input) // OUTPUT_BIT_COUNT):])

    @always_seq(Clk.posedge, reset=Reset)
    def goto_next():
        idx.next = idx + 1
        Output.next = Input[idx + OUTPUT_BIT_COUNT:idx]

    return instances()

@block
def chunk_buffer_sim(Clk, Reset, Input, Output):
    chunk_buffer0 = chunk_buffer(Clk, Reset, Input, Output)

    tCK = 20
    tReset = int(tCK * 3.5)
    
    @instance
    def tb_clk():
        Clk.next = False
        yield delay(int(tCK // 2))
        while True:
            Clk.next = not Clk
            yield delay(int(tCK // 2))

    @instance
    def tb_logic():
        Reset.next = 1
        yield delay(tReset)
        Reset.next = 0

        Input.next = 0xABCDEF
        
        for i in range(100):
            yield delay(int(tCK // 2))
        raise StopSimulation
            
    return instances()

def test_top_level_interfaces_verify():
    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, True)
    Input = Signal(intbv(0)[256:])
    Output = Signal(intbv(0)[8:])
    
    top_sim = chunk_buffer_sim(Clk, Reset, Input, Output)
    assert conversion.analyze(top_sim) == 0

    top = chunk_buffer(Clk, Reset, Input, Output)
    top.name = 'ChunkBuffer'
    top.convert('Verilog')
    top.convert('VHDL')
