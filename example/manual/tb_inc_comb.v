module tb_inc_comb;

wire [7:0] nextCount;
reg [7:0] count;

initial begin
    $from_myhdl(
        count
    );
    $to_myhdl(
        nextCount
    );
end

inc_comb dut(
    nextCount,
    count
);

endmodule
