'''
Created on 3 dec. 2024

@author: josy
'''

from myhdl import (HdlClass, Signal, intbv, block, always_seq, instances, OpenPort, always_comb,
                   Constant)


class Counter(HdlClass):

    def __init__(self, RANGE, Clk, Reset, SClr, CntEn, Q=None, IsMax=None, WRAP_AROUND=False):
        '''
            RANGE: int : number of counts
            Clk: Signal(bool()): the domain clock
            Reset: ResetSignal(): its associated reset
            SClr: Signal(bool()): resets the count
            CntEn: Signal(bool()): advances count
            Q: Signal(intbv()[w:]): the actual count
        '''
        self.Clk = Clk
        self.Reset = Reset
        self.SClr = SClr
        self.CntEn = CntEn
        self.RANGE = RANGE
        self.Q = Q if Q is not None else Signal(intbv(0, 0, RANGE))
        self.IsMax = IsMax if IsMax is not None else Signal(bool(0))
        self.WRAP_AROUND = WRAP_AROUND

    @block(skipname=True)
    def hdl(self):
        if isinstance(self.Q, OpenPort):
            count = Signal(intbv(0, 0, self.RANGE))
        else:
            count = self.Q.duplicate()

        if self.WRAP_AROUND:

            @always_seq(self.Clk.posedge, reset=self.Reset)
            def upcounter():
                if self.SClr or self.CntEn:
                    if self.SClr:
                        count.next = 0
                    else:
                        if count < (self.RANGE - 1):
                            count.next = count + 1
                        else:
                            count.next = 0

        else:

            @always_seq(self.Clk.posedge, reset=self.Reset)
            def upcounter():
                if self.SClr or self.CntEn:
                    if self.SClr:
                        count.next = 0
                    else:
                        if count < (self.RANGE - 1):
                            count.next = count + 1

        @always_comb
        def mkq():
            self.Q.next = count
            self.IsMax.next = (count == self.RANGE - 1)

        return self.hdlinstances()


class Tone(HdlClass):

    def __init__(self, DIVIDER, Clk, Reset, Key, Wave=None):
        self.DIVIDER = DIVIDER
        self.Clk = Clk
        self.Reset = Reset
        self.Key = Key
        self.Wave = Wave if Wave is not None else Signal(bool())

    @block(skipname=True)
    def hdl(self):
        divider = Counter(self.DIVIDER, self.Clk, self.Reset, Constant(bool(0)), Constant(bool(1)),
                          Q=OpenPort(), WRAP_AROUND=True)

        @always_seq(self.Clk.posedge, reset=self.Reset)
        def squarewave():
            if not self.Key:
                self.Wave.next = 0
            else:
                if divider.IsMax:
                    self.Wave.next = not self.Wave

        return self.hdlinstances()


if __name__ == '__main__':

    from myhdl import ResetSignal

    class KakaFonie(HdlClass):

        def __init__(self, Clk, Reset, Keys, Noise):
            self.Clk = Clk
            self.Reset = Reset
            self.Keys = Keys
            self.Noise = Noise if Noise is not None else Signal(bool(0))

        @block(skipname=True)
        def hdl(self):
            FREQUENCIES = [261.626, 277.183, 293.665, 311.127, 329.628, 349.228, 369.994, 391.995, 415.305, 440.0, 466.167, 493.883]

            wavegenerator = []
            # waves = [Signal(bool(0)) for __ in range(12)]
            for i in range(12):
                DIVIDER = int(50e6 / FREQUENCIES[i])
                # wavegenerator.append(Tone(DIVIDER, self.Clk, self.Reset, self.Keys(1), waves[i]))
                wavegenerator.append(Tone(DIVIDER, self.Clk, self.Reset, self.Keys(i)))

            waves = [wavegenerator[i].Wave for i in range(12)]

            @always_comb
            def makenoise():
                self.Noise.next = 0
                for i in range(12):
                    if waves[i]:
                        self.Noise.next = self.Noise | 1

            return self.hdlinstances()

    # try converting
    Clk = Signal(bool(0))
    Reset = ResetSignal(0, 1, False)
    Keys = Signal(intbv(0)[12:])
    Noise = Signal(bool(0))

    if 1:
        ''' looks like we have to live with writing a wrapper '''

        # a local written-out wrapper works fine
        @block
        def wrapper(Clk, Reset, Keys, Noise):
            dfc = KakaFonie(Clk, Reset, Keys, Noise)
            # print(f'{vars(dfc)=}')
            dfchdl = dfc.hdl()
            # print(f'{vars(dfchdl)=}')
            return dfchdl

        dfc = wrapper(Clk, Reset, Keys, Noise)
        dfc.convert(hdl='VHDL', name='KakaFonie')
        dfc.convert(hdl='Verilog', name='KakaFonie')
    # these fail in one way or another
    # else:
    #     from _hdlclass import wrapper, convert
    #     if 1:
    #         # this raises an IndexError in _analyze.py
    #         # beacuse the '*args' in wrapper disappear into nowhere?
    #         convert(wrapper(XYMotors, PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive))
    #     else:
    #         # this produces an 'empty' entity
    #         hc = XYMotors(PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive)
    #         hc.convert(hdl='VHDL', name='XYMotors')

