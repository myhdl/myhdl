module tb;
   
   reg [16:0] a;
   reg [4:0] b;
   wire [9:0] c;

   // reg[6:0] areg;
   // reg[4:0] breg;
   

   mod dut (a, b, c);
   
   initial
     begin
	$to_myhdl(a, b, c);
	$from_myhdl(b);
     end
   

   initial begin
      a = 0;
      b = 0;
      repeat(5) begin
	 # 10;
	 // $display("time %d", $time);
	 a = a + 1;
	 # 10;
	 b = b + 1;
      end
   end

   // assign a = areg;
   // assign b = breg;

   always @ (a, b, c) begin
      $display("verilog %d %d %d", a, b, c);
   end
   
   
   
endmodule // tb

    
