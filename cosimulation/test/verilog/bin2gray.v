module bin2gray(B, G);

   parameter width = 8;
   input [width-1:0]  B;
   output [width-1:0] G;
   reg [width-1:0] G;
   integer i;
   wire [width:0] extB;

   assign extB = {1'b0, B};

   always @(extB) begin
      for (i=0; i < width; i=i+1)
	G[i] <= extB[i+1] ^ extB[i];
   end

endmodule // bin2gray
