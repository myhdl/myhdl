module tb;
   
   reg [16:0] a;
   reg [4:0] b;
   reg [9:0] c;
   reg 	     clk;
   
  
   initial
     begin
	$to_myhdl(c);
	$from_myhdl(a, b);
     end

   always @ (a, b) begin
      c = a + b;
      $display("Verilog: %d c =%d a=%d b=%d", $time, c, a, b);
      
   end

   initial begin
      clk = 0;

      forever begin
	 clk = #50 ~clk;
      end
   end
   
   
endmodule // tb

    
