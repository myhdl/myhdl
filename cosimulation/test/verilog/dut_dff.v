module dut_dff;

   reg	d;
   reg 	clk;
   reg 	reset;
   wire q;

   initial begin
      $from_myhdl(d, clk, reset);
      $to_myhdl(q);
   end

   dff dut (.q(q), .d(d), .clk(clk), .reset(reset));

endmodule // inc
