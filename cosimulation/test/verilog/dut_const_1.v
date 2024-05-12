module dut_const_1;

   reg 	clk;
   wire q;

   initial begin
      $from_myhdl(clk);
      $to_myhdl(q);
   end

   const_1 dut (.q(q), .clk(clk) );

endmodule // inc
