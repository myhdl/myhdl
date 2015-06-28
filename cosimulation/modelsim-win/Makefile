INCS := C:\\modeltech64_10.4\\include
LIB_PATH := C:\\modeltech64_10.4\\win64

ifneq ($(filter cl%,$(CC)),)
	CFLAGS := /LD /I$(INCS)
	LIBFLAGS := $(LIB_PATH)\\mtipli.lib
else
	CFLAGS := -static -g -I$(INCS) -o myhdl_vpi.dll
	LIBFLAGS := -L$(LIB_PATH) -lmtipli
endif

all: myhdl_vpi.dll

myhdl_vpi.dll: myhdl_vpi.c
	$(CC) $(CFLAGS) $< $(LIBFLAGS)

clean:
	@del /q myhdl_vpi.dll || rm -rf myhdl_vpi.dll 2>&1> /dev/null ||:
	@del /q myhdl_vpi.lib || rm -rf myhdl_vpi.lib 2>&1> /dev/null ||:
	@del /q myhdl_vpi.exp || rm -rf myhdl_vpi.exp 2>&1> /dev/null ||:
	@del /q myhdl_vpi.obj || rm -rf myhdl_vpi.obj 2>&1> /dev/null ||:
