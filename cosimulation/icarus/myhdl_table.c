# include "vpi_user.h"

extern void myhdl_register();

void (*vlog_startup_routines[])() = {
      myhdl_register,
      0
};
