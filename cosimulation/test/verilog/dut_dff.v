module dut_dff;

   reg	d;
   reg 	clock;
   reg 	reset;
   wire q;

   initial begin
      $from_myhdl(d, clock, reset);
      $to_myhdl(q);
   end

   dff dut (.q(q), .d(d), .clock(clock), .reset(reset));

endmodule // inc
