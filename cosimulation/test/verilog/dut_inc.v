module dut_inc;

   reg	enable;
   reg 	clock;
   reg 	reset;
   wire [15:0] count;

   initial begin
      $from_myhdl(enable, clock, reset);
      $to_myhdl(count);
   end

   inc dut (.count(count), .enable(enable), .clock(clock), .reset(reset));
   defparam dut.n= `n;

endmodule // inc
