// DESCRIPTION: Example MyHDL cosimulation with verilator
//======================================================================

//** This file is not compiled standalone, instead verilator_myhdl_wrapper makes {model}__myhdl.cpp which #includes it
// (This is because we cannot make a single verilator_myhdl_main.o; it has different code for each model)

#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <verilated.h>

#define MAXLINE 4096
#define MAXWIDTH 10
#define MAXARGS 1024

#ifndef MODEL
# error "MODEL must be set to the name of the top level model, e.g. Vtop"
#endif

// Include model header, generated from Verilating
// This converts MODEL, a define with a value, into #include "<MODELs_value>.h"
#define QUOTEX(t) #t
#define QUOTE(t) QUOTEX(t)
#define PLACE(t) t
#define INCLUDE(path,suffix) QUOTE(PLACE(path)PLACE(suffix))

#include INCLUDE(MODEL,.h)

// If "verilator --trace" is used, include the tracing class
#if VM_TRACE
# include <verilated_vcd_c.h>
#endif

// Current simulation time (64-bit unsigned)
vluint64_t main_time = 0;
// Called by $time in Verilog
double sc_time_stamp () {
    return main_time; // Note does conversion to real, to match SystemC
}

int main(int argc, char** argv, char** env) {
    // This is a more complicated example, please also see the simpler examples/hello_world_c.

    // Prevent unused variable warnings
    if (0 && argc && argv && env) {}
    // Pass arguments so Verilated code can see them, e.g. $value$plusargs
    Verilated::commandArgs(argc, argv);

    // Set debug level, 0 is off, 9 is highest presently used
    Verilated::debug(0);

    // Randomization reset policy
    Verilated::randReset(2);

    // Construct the Verilated model, from Verilating
    MODEL* top = new MODEL;

    // Setup variable list and myhdl
    myhdl_io_setup(top);
    myhdl_init();

    // If verilator was invoked with --trace, open trace
#if VM_TRACE
    Verilated::traceEverOn(true);  // Verilator must compute traced signals
    VL_PRINTF("Enabling waves into vlt_dump.vcd...\n");
    VerilatedVcdC* tfp = new VerilatedVcdC;
    top->trace(tfp, 99);  // Trace 99 levels of hierarchy
    tfp->open("vlt_dump.vcd");  // Open the dump file
#endif

    // Simulate until $finish
    myhdl_push_outputs();

    while (!Verilated::gotFinish()) {
        myhdl_pull_inputs();

        vluint64_t new_time = pli_time*1000 + delta;
        assert(main_time<=new_time);
        main_time = new_time;

        top->eval();

        myhdl_push_outputs();
    }

    // Final model cleanup
    top->final();

    // Close trace if opened
#if VM_TRACE
    if (tfp) { tfp->close(); }
#endif

    //  Coverage analysis (since test passed)
#if VM_COVERAGE
    VerilatedCov::write("coverage.dat");
#endif

    // Destroy model
    delete top; top = NULL;

    // Fin
    exit(0);
}
