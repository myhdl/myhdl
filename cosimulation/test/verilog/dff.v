module dff(q, d, clk, reset);

   input d;
   input clk;
   input reset;
   output q;
   reg 	  q;

   always @(posedge clk or negedge reset) begin
      if (reset == 0) begin
	 q <= 0;
      end
      else begin
	 q <= d;
      end
   end // always @ (posedge clk or negedge reset)

endmodule // inc
