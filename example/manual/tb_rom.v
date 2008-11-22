module tb_rom;

wire [7:0] dout;
reg [3:0] addr;

initial begin
    $from_myhdl(
        addr
    );
    $to_myhdl(
        dout
    );
end

rom dut(
    dout,
    addr
);

endmodule
