module dff(q, d, clock, reset);

   input d;
   input clock;
   input reset;
   output q;
   reg 	  q;

   always @(posedge clock or negedge reset) begin
      if (reset == 0) begin
	 q <= 0;
      end
      else begin
	 q <= d;
      end
   end // always @ (posedge clock or negedge reset)

endmodule // inc
