module dut_dff_clkout;

   wire clkout;
   reg	d;
   reg 	clk;
   reg 	reset;
   wire q;

   initial begin
      $from_myhdl(d, clk, reset);
      $to_myhdl(clkout, q);
   end

   dff_clkout dut (.clkout(clkout), .q(q), .d(d), .clk(clk), .reset(reset));
   
endmodule
