module tb_bin2gray;

reg [7:0] B;
wire [7:0] G;

initial begin
    $from_myhdl(
        B
    );
    $to_myhdl(
        G
    );
end

bin2gray dut(
    B,
    G
);

endmodule
