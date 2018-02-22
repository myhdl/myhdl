import myhdl
from myhdl import *

def uart_tx(tx_bit, tx_valid, tx_byte, tx_clk, tx_rst):
    
    index = Signal(intbv(0, min=0, max=8))
    st = enum('IDLE', 'START', 'DATA')
    state = Signal(st.IDLE)
    
    @always(tx_clk.posedge, tx_rst.negedge)
    def fsm():
        if tx_rst == 0:
            tx_bit.next = 1
            index.next = 0
            state.next = st.IDLE
        else:
            if state == st.IDLE:
                tx_bit.next = 1
                if tx_valid: # a pulse
                    state.next = st.START
            elif state == st.START:
                tx_bit.next = 0
                index.next = 7
                state.next = st.DATA
            elif state == st.DATA:
                tx_bit.next = tx_byte[index]
                if index == 0:
                    state.next = st.IDLE
                else:
                    index.next = index - 1
                    
    return fsm

def uart_tx_2(tx_bit, tx_valid, tx_byte, tx_clk, tx_rst):
    
    index = Signal(intbv(0, min=0, max=8))
    st = enum('IDLE', 'START', 'DATA')
    state = Signal(st.IDLE)
    
    @always_seq(tx_clk.posedge, reset=tx_rst)
    def fsm():
        if state == st.IDLE:
            tx_bit.next = 1
            if tx_valid: # a pulse
                state.next = st.START
        elif state == st.START:
            tx_bit.next = 0
            index.next = 7
            state.next = st.DATA
        elif state == st.DATA:
            tx_bit.next = tx_byte[index]
            if index == 0:
                state.next = st.IDLE
            else:
                index.next = index - 1
                    
    return fsm



def tb(uart_tx):   
      
    tx_bit = Signal(bool(1))
    tx_valid = Signal(bool(0))
    tx_byte = Signal(intbv(0)[8:])
    tx_clk = Signal(bool(0))
    # tx_rst = Signal(bool(1))
    tx_rst = ResetSignal(1, active=0, async=True)
   
    uart_tx_inst = uart_tx(tx_bit, tx_valid, tx_byte, tx_clk, tx_rst)
    
    # toVerilog(uart_tx, tx_bit, tx_valid, tx_byte, tx_clk, tx_rst)
    
    @always(delay(10))
    def clk_gen():
        tx_clk.next = not tx_clk
            
    @instance
    def stimulus():
        tx_rst.next = 1
        yield delay(100)
        tx_rst.next = 0
        yield delay(100)
        tx_rst.next = 1
        yield delay(100)
        for v in (0x00, 0xff, 0x55, 0xaa):
            yield tx_clk.negedge
            tx_byte.next = v
            tx_valid.next = 1
            yield tx_clk.negedge
            tx_valid.next = 0
            yield delay(16 * 20)
        raise StopSimulation
    
    return clk_gen, stimulus, uart_tx_inst


sim = Simulation(traceSignals(tb, uart_tx_2))

sim.run()
        
    
    
    

        
    

                
            
    