
from myhdl import *

def m_firfilt_fixbv(clock, reset, sig_in, sig_out, coef):
    """
    """
    taps = [Signal(fixbv(0, shift=sig_in.shift, min=sig_in.min, max=sig_in.max))
            for ii in range(len(coef))]
    
    # @todo: check the coefficients, needs to be the correct type
    # could even detect float here, scale and convert to int
    coef = tuple(coef)  
    mshift = len(sig_in)-1
    @always(clock.posedge)
    def rtl_sop():
        if reset:
            for ii in range(len(coef)):
                taps[ii].next = 0
            sig_out.next = 0
        else:
            sop = 0.0
            # Note this adds an extra delay! (Group delay N/2+1)
            for ii in range(len(coef)):
                if ii == 0:
                    taps[ii].next = sig_in 
                else: 
                    taps[ii].next = taps[ii-1]
                c = coef[ii]
                sop = sop + (taps[ii] * c)
            sig_out.next = (sop >> mshift)    
    
    return rtl_sop
