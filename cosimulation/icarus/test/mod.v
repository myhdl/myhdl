module mod(a, b, c);

   input [16:0] a;
   input [4:0] b;
   output [9:0] c;
   reg [9:0] 	c;

   initial begin
      c = 0;
   end
   
   
      
always @ (a or b)
  begin
     $display("trigger");
     
     c = a + b;
  end
   
endmodule
   
