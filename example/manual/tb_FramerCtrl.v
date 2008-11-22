module tb_FramerCtrl;

wire SOF;
wire [2:0] state;
reg syncFlag;
reg clk;
reg reset_n;

initial begin
    $from_myhdl(
        syncFlag,
        clk,
        reset_n
    );
    $to_myhdl(
        SOF,
        state
    );
end

FramerCtrl dut(
    SOF,
    state,
    syncFlag,
    clk,
    reset_n
);

endmodule
