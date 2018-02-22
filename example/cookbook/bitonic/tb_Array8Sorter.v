module tb_Array8Sorter;

reg [3:0] a0;
reg [3:0] a1;
reg [3:0] a2;
reg [3:0] a3;
reg [3:0] a4;
reg [3:0] a5;
reg [3:0] a6;
reg [3:0] a7;
wire [3:0] z0;
wire [3:0] z1;
wire [3:0] z2;
wire [3:0] z3;
wire [3:0] z4;
wire [3:0] z5;
wire [3:0] z6;
wire [3:0] z7;

initial begin
    $from_myhdl(
        a0,
        a1,
        a2,
        a3,
        a4,
        a5,
        a6,
        a7
    );
    $to_myhdl(
        z0,
        z1,
        z2,
        z3,
        z4,
        z5,
        z6,
        z7
    );
end

Array8Sorter dut(
    a0,
    a1,
    a2,
    a3,
    a4,
    a5,
    a6,
    a7,
    z0,
    z1,
    z2,
    z3,
    z4,
    z5,
    z6,
    z7
);

endmodule
