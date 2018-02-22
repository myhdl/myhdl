module tb_gray_inc_reg;

wire [7:0] graycnt;
reg enable;
reg clock;
reg reset;

initial begin
    $from_myhdl(
        enable,
        clock,
        reset
    );
    $to_myhdl(
        graycnt
    );
end

gray_inc_reg dut(
    graycnt,
    enable,
    clock,
    reset
);

endmodule
