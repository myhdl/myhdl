module inc(count, enable, clock, reset);

   parameter n = 8;
   input enable;
   input clock;
   input reset;
   output [15:0] count;
   reg [15:0] count;

   always @(posedge clock or negedge reset) begin
      if (reset == 0) begin
	 count <= 0;
      end
      else begin
	 if (enable) begin
	    count <= (count + 1) % n;
	 end
	 // $display("count %d", count);
      end
   end

endmodule // inc
