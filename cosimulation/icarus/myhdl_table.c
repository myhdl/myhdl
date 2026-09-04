# include "vpi_user.h"

extern void myhdl_register(void);

void (*vlog_startup_routines[])(void) = {
      myhdl_register,
      0
};
