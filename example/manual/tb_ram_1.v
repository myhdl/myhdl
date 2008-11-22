module tb_ram_1;

wire [7:0] dout;
reg [7:0] din;
reg [6:0] addr;
reg we;
reg clk;

initial begin
    $from_myhdl(
        din,
        addr,
        we,
        clk
    );
    $to_myhdl(
        dout
    );
end

ram_1 dut(
    dout,
    din,
    addr,
    we,
    clk
);

endmodule
