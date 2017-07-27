module tb_inc;

wire [7:0] count;
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
        count
    );
end

inc dut(
    count,
    enable,
    clock,
    reset
);

endmodule
