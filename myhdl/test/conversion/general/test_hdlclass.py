'''
Created on 3 dec. 2024

@author: josy
'''

from myhdl import (HdlClass, Signal, intbv, block, always_seq, OpenPort, always_comb,
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
            count = self.Q

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
        def mkismax():
            self.IsMax.next = (count == self.RANGE - 1)

        return self.hdlinstances()


class PwmCounter(HdlClass):

    def __init__(self, RANGE, Clk, Reset, PwmValue, PwmOut=None):
        self.RANGE = RANGE
        self.Clk = Clk
        self.Reset = Reset
        self.PwmValue = PwmValue
        self.PwmOut = PwmOut if PwmOut is not None else Signal(bool(0))

    @block
    def hdl(self):
        counter = Counter(self.RANGE, self.Clk, self.Reset, SClr=Constant(bool(0)), CntEn=Constant(bool(1)), IsMax=OpenPort(), WRAP_AROUND=True)

        @always_seq(self.Clk.posedge, reset=self.Reset)
        def pwm():
            if counter.Q >= self.PwmValue:
                self.PwmOut.next = 0
            else:
                self.PwmOut.next = 1

        return self.hdlinstances()


if __name__ == '__main__':

    from myhdl import ResetSignal, instance, delay, StopSimulation, instances

    class XYMotors(HdlClass):

        def __init__(self, PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive):
            # mess up the order of the signals trying to confuse the convertor
            # as we have to tweak things a bit to achieve 'direct' conversion of
            # HdlClass objects
            self.Reset = Reset
            self.XDrive = XDrive
            self.PWMCOUNT = PWMCOUNT
            self.Clk = Clk
            self.XSpeed = XSpeed
            self.YSpeed = YSpeed
            self.YDrive = YDrive

        @block(skipname=True)
        def hdl(self):
            xmotor = PwmCounter(self.PWMCOUNT, self.Clk, self.Reset, self.XSpeed, self.XDrive)
            ymotor = PwmCounter(self.PWMCOUNT, self.Clk, self.Reset, self.YSpeed, self.YDrive)

            return self.hdlinstances()

    # create a minimal test-bench to test the .vcd generation
    # as we want/have to weed out the `None` - because of an @block(skipname=True)
    # which add an unnecessary indentation level in the waveform which absolutely looks ugly
    @block
    def tb_xymotors():
        PWMCOUNT = 100
        Clk = Signal(bool(0))
        Reset = ResetSignal(0, 1, False)
        XSpeed = Signal(intbv(0, 0, PWMCOUNT))
        YSpeed = Signal(intbv(0, 0, PWMCOUNT))
        XDrive = Signal(bool(0))
        YDrive = Signal(bool(0))

        dft = XYMotors(PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive)
        dfthdl = dft.hdl()
        dfthdl.name = 'XYMotors'

        tCK = 10

        @instance
        def genclkreset():
            Reset.next = 1
            for dummy in range(3):
                Clk.next = 1
                yield delay(tCK // 2)
                Clk.next = 0
                yield delay(tCK - tCK // 2)

            Clk.next = 1
            yield delay(tCK // 2)
            Clk.next = 0
            Reset.next = 0
            yield delay(tCK - tCK // 2)
            while True:
                Clk.next = 1
                yield delay(tCK // 2)
                Clk.next = 0
                yield delay(tCK - tCK // 2)

        @instance
        def stimulus():
            for dummy in range(10):
                yield Clk.posedge

            raise StopSimulation

        return instances()

    if 0:
        dft = tb_xymotors()
        dft.config_sim(trace=True, timescale='1ps', tracebackup=False)
        dft.run_sim()

    def convert():
        # try converting
        # note they will appear in this order in the entity/module declaration; why?
        XDrive = Signal(bool(0))
        PWMCOUNT = 100
        Reset = ResetSignal(0, 1, False)
        Clk = Signal(bool(0))
        XSpeed = Signal(intbv(0, 0, PWMCOUNT))
        YSpeed = Signal(intbv(0, 0, PWMCOUNT))
        YDrive = Signal(bool(0))

        if 0:
            ''' looks like we have to live with writing a wrapper '''

            # a local written-out wrapper works fine
            @block(skipname=True)
            def wrapper(PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive):
                dfc = XYMotors(PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive)
                dfchdl = dfc.hdl()
                # ! DO NOT override the name
                # e.g.: dfchdl.name = 'blabla' will prefix all names with 'blabla'
                return dfchdl

            dfc = wrapper(PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive)
            dfc.convert(hdl='VHDL', name='XYMotors')
            dfc.convert(hdl='Verilog', name='XYMotors')

        else:
            if 0:

                @block
                def wrapper(hdlclass, *args):
                    return hdlclass(*args).hdl()

                # this raises an IndexError in _analyze.py
                # beacuse the '*args' in wrapper disappear into nowhere?
                dfc = wrapper(XYMotors, PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive)
                for key, value in vars(dfc).items():
                    print(key, value)
                print()
                print(f'{dfc.sigdict=}')
                dfc.convert(hdl='VHDL', name='XYMotors')
            else:
                # doing direct conversion from the class instance itself
                # this is quite necessary for hierarchical conversion
                dfc = XYMotors(PWMCOUNT, Clk, Reset, XSpeed, YSpeed, XDrive, YDrive)
                dfc.convert(hdl='VHDL', name='XYMotors')
                dfc.convert(hdl='Verilog', name='XYMotors')

    convert()
