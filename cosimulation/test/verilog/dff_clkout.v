module dff_clkout(clkout, q, d, clk, reset);

   input d;
   input clk;
   input reset;
   output clkout;
   reg clkout;
   output q;
   reg 	  q;

   always @(posedge clkout or negedge reset) begin
      if (reset == 0) begin
	 q <= 0;
      end
      else begin
	 q <= d;
      end
   end // always @ (posedge clk or negedge reset)

   initial begin
      clkout = 0;
      q = 0;
   end
      
   always @(clk)
       clkout = clk;
   

endmodule // inc
