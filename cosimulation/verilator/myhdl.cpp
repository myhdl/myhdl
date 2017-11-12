#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "vpi_user.h"
#include "verilated.h"

#define MAXLINE 4096  // WARNING there is no checking for buffer overflow! This fits only ~~80 signals
#define MAXWIDTH 10
// #define DEBUG 1

/* Sized variables */
#ifndef PLI_TYPES
#define PLI_TYPES
typedef int             PLI_INT32;
typedef unsigned int    PLI_UINT32;
typedef short           PLI_INT16;
typedef unsigned short  PLI_UINT16;
typedef char            PLI_BYTE8;
typedef unsigned char   PLI_UBYTE8;
#endif

/* 64 bit type for time calculations */
typedef unsigned long long myhdl_time64_t;

static myhdl_time64_t myhdl_time;
static myhdl_time64_t verilog_time;
static myhdl_time64_t pli_time;
static int delta;

static int rpipe;
static int wpipe;

static char bufcp[MAXLINE];


#ifdef MYHDL_TRAFFIC_DEBUG
FILE* myfp() {
  static FILE* fp = NULL;
  if (!fp) {
    char filename[1000];
    for (int i=0; i<1000; ++i) {
      sprintf(filename, "traffic_%04d.log", i);
      fp = fopen(filename, "r");
      if (fp) fclose(fp);
      else break;
    }
    fprintf(stderr, "Opened %s\n", filename);
    fp = fopen(filename,"w");
    if (!fp) {
      vpi_printf((PLI_BYTE8*)"ERROR: cannot open traffic.log\n");
      return NULL;
    }
  }
  return fp;
}

ssize_t mywrite(int fd, const void *buf, size_t count) {
  ssize_t got = write(fd, buf, count);
  char buf2[MAXLINE];
  memcpy(buf2, buf, count);
  buf2[count] = '\0';
  fprintf(myfp(),"-myhdl-wr-%d %s\n", (int)got, buf2);
  fflush(myfp());
  return got;
}
ssize_t myread(int fd, void *buf, size_t count) {
  ssize_t got = read(fd, buf, count);
  if (got>0) {
    char buf2[MAXLINE];
    memcpy(buf2, buf, count);
    buf2[got] = '\0';
    fprintf(myfp(),"-myhdl-rd-%d %s\n", (int)got, buf2);
  } else {
    fprintf(myfp(),"-myhdl-rd EOF %d\n", (int)got);
  }
  fflush(myfp());
  return got;
}
#else
# define myread read
# define mywrite write
#endif

static myhdl_time64_t timestruct_to_time(const struct t_vpi_time*ts)
{
  myhdl_time64_t ti = ts->high;
  ti <<= 32;
  ti += ts->low & 0xffffffff;
  return ti;
}

static int init_pipes()
{
  // Internal func called at startup to initialize pipe
  char *w;
  char *r;

  static int init_pipes_flag = 0;

  if (init_pipes_flag) {
    return(0);
  }

  if ((w = getenv("MYHDL_TO_PIPE")) == NULL) {
    vpi_printf((PLI_BYTE8*)"ERROR: no mywrite pipe to myhdl\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  if ((r = getenv("MYHDL_FROM_PIPE")) == NULL) {
    vpi_printf((PLI_BYTE8*)"ERROR: no myread pipe from myhdl\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  wpipe = atoi(w);
  rpipe = atoi(r);
  init_pipes_flag = 1;
  return (0);
}

static void myhdl_init()
{
  // Called once by model at start
  s_vpi_time verilog_time_s;
  char buf[MAXLINE];
  char s[MAXWIDTH];
  int n;

  static int from_myhdl_flag = 0;

  if (from_myhdl_flag) {
    vpi_printf((PLI_BYTE8*)"ERROR: myhdl_init() called more than once\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return;
  }
  from_myhdl_flag = 1;

  init_pipes();

  verilog_time_s.type = vpiSimTime;
  vpi_get_time(NULL, &verilog_time_s);
  verilog_time = timestruct_to_time(&verilog_time_s);
  if (verilog_time != 0) {
    vpi_printf((PLI_BYTE8*)"ERROR: myhdl_init() should be called at time 0\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return;
  }
  sprintf(buf, "FROM 0 ");
  pli_time = 0;
  delta = 0;

  for (myhdl_signal* sigp = myhdl_inputs; sigp->name; ++sigp) {
    strcat(buf, sigp->name);
    strcat(buf, " ");
    sprintf(s, "%d ", sigp->bits);
    strcat(buf, s);
  }
  // write: FROM 0 <sig0name> <sig0size> <sig1name> <sig1size>...
  n = mywrite(wpipe, buf, strlen(buf));  // TODO check for overflow

  // read: OK
  if ((n = myread(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf((PLI_BYTE8*)"Info: MyHDL simulator down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return;
  }
  assert(n > 0);
  buf[n] = '\0';

  sprintf(buf, "TO 0 ");

  int i=0;
  for (myhdl_signal* sigp = myhdl_outputs; sigp->name; ++sigp) {
    strcat(buf, sigp->name);
    strcat(buf, " ");
    sprintf(s, "%d ", sigp->bits);
    strcat(buf, s);
  }
  // write: TO 0 <sig0name> <sig0size> <sig1name> <sig1size>...
  n = mywrite(wpipe, buf, strlen(buf));

  // read: OK
  if ((n = myread(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf((PLI_BYTE8*)"Info: MyHDL simulator down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return;
  }
  assert(n > 0);
  buf[n] = '\0';

  return;
}


static void myhdl_push_outputs()
{
  // Called to send primary outputs and get new timestamp
  s_vpi_time verilog_time_s;
  s_vpi_time time_s;
  char buf[MAXLINE];
  char append[MAXLINE];
  int n;
  int i;
  char *myhdl_time_string;
  myhdl_time64_t delay;

  static int start_flag = 1;

  int all_signals = 0;
  if (start_flag) {
    start_flag = 0;
    // write: START
    n = mywrite(wpipe, "START", 5);
    // vpi_printf((PLI_BYTE8*)"INFO: RO cb at start-up\n");
    // read: OK
    if ((n = myread(rpipe, buf, MAXLINE)) == 0) {
      vpi_printf((PLI_BYTE8*)"ABORT from RO cb at start-up\n");
      vpi_control(vpiFinish, 1);  /* abort simulation */
    }
    assert(n > 0);
    all_signals = 1;
  }

  buf[0] = '\0';
  verilog_time_s.type = vpiSimTime;
  vpi_get_time(NULL, &verilog_time_s);
  verilog_time = timestruct_to_time(&verilog_time_s);
  if (verilog_time != (pli_time * 1000 + delta)) {
    vpi_printf((PLI_BYTE8*)"%u %u\n", verilog_time_s.high, verilog_time_s.low );
    vpi_printf((PLI_BYTE8*)"%llu %llu %d\n", verilog_time, pli_time, delta);
  }
  assert( (verilog_time & 0xFFFFFFFF) == ( (pli_time * 1000 + delta) & 0xFFFFFFFF ) );
  sprintf(buf, "%llu ", pli_time);

  i = 0;
  for (myhdl_signal* sigp = myhdl_outputs; sigp->name; ++sigp) {
    append[0] = '\0';
    if (sigp->bits <= 8) {
      if (*((vluint8_t*)sigp->prevp) != *((vluint8_t*)sigp->datap) || all_signals) {
        sprintf(append, "%x", *((vluint8_t*)sigp->datap));
        *((vluint8_t*)sigp->prevp) = *((vluint8_t*)sigp->datap);
      }
    }
    else if (sigp->bits <= 16) {
      if (*((vluint16_t*)sigp->prevp) != *((vluint16_t*)sigp->datap) || all_signals) {
        sprintf(append, "%x", *((vluint16_t*)sigp->datap));
        *((vluint16_t*)sigp->prevp) = *((vluint16_t*)sigp->datap);
      }
    }
    else if (sigp->bits <= 32) {
      if (*((vluint32_t*)sigp->prevp) != *((vluint32_t*)sigp->datap) || all_signals) {
        sprintf(append, "%x", *((vluint32_t*)sigp->datap));
        *((vluint32_t*)sigp->prevp) = *((vluint32_t*)sigp->datap);
      }
    }
    else if (sigp->bits <= 64) {
      if (*((vluint64_t*)sigp->prevp) != *((vluint64_t*)sigp->datap) || all_signals) {
        sprintf(append, "%" VL_PRI64 "x", *((vluint64_t*)sigp->datap));
        *((vluint64_t*)sigp->prevp) = *((vluint64_t*)sigp->datap);
      }
    }
    else {
      WDataOutP prevp = ((WDataOutP)sigp->prevp);
      WDataInP datap = ((WDataInP)sigp->datap);
      if (!VL_EQ_W(VL_WORDS_I(sigp->bits), prevp, datap) || all_signals) {
        for (int w=VL_WORDS_I(sigp->bits)-1; w>=0; --w) {
          char hex[20];
          sprintf(hex, "%08x", datap[w]);
          strcat(append, hex);
        }
        VL_ASSIGN_W(sigp->bits, prevp, datap);
      }
    }
    if (append[0]) {
      strcat(buf, sigp->name);
      strcat(buf, " ");
      strcat(buf, append);
      strcat(buf, " ");
    }
    i++;
  }
  // write: <timehi> <timelo> <veriloghi> <veriloglo> <sig0name> <sig0hexval>...
  n = mywrite(wpipe, buf, strlen(buf));
  // read: <myhdl_time> [<sig0value> <sig1value>...]
  if ((n = myread(rpipe, buf, MAXLINE)) == 0) {
    // vpi_printf((PLI_BYTE8*)"ABORT from RO cb\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return;
  }
  assert(n > 0);
  buf[n] = '\0';

  // save copy for later callback
  strcpy(bufcp, buf);

  // decide how to advance time
  myhdl_time_string = strtok(buf, " ");
  myhdl_time = (myhdl_time64_t) strtoull(myhdl_time_string, (char **) NULL, 10);
  delay = (myhdl_time - pli_time) * 1000;
  assert(delay <= 0xFFFFFFFF);
  if (delay > 0) { // schedule cbAfterDelay callback
    assert(delay > delta);
    delay -= delta;
    delta = 0;
    pli_time = myhdl_time;
  } else {
    delta++;
    assert(delta < 1000);
  }
  return;
}

static void myhdl_pull_inputs()
{
  // Called to get primary inputs
  if (delta == 0) {
    return;
  }

  // skip time value
  strtok(bufcp, " ");

  for (myhdl_signal* sigp = myhdl_inputs; sigp->name; ++sigp) {
    const char* str = strtok(NULL, " ");
    if (str==NULL) break;
    vluint64_t value = strtoll(str, NULL, 16);
    if (sigp->bits <= 8) {
        *((vluint8_t*)sigp->datap) = VL_CLEAN_II(sigp->bits, sigp->bits, value);
    }
    else if (sigp->bits <= 16) {
        *((vluint16_t*)sigp->datap) = VL_CLEAN_II(sigp->bits, sigp->bits, value);
    }
    else if (sigp->bits <= 32) {
        *((vluint32_t*)sigp->datap) = VL_CLEAN_II(sigp->bits, sigp->bits, value);
    }
    else if (sigp->bits <= 64) {
        *((vluint64_t*)sigp->datap) = VL_CLEAN_QQ(sigp->bits, sigp->bits, value);
    }
    else {
      WDataOutP datap = ((WDataOutP)sigp->datap);
      VL_ZERO_W(sigp->bits, datap);
      const char* lsbp = str;  // character with LSB
      while (*lsbp && isxdigit(*(lsbp+1))) ++lsbp;
      int bit = 0;
      while (lsbp >= str) {
          int digit = toupper(*lsbp);  if (digit>='A') digit -= 'A';
          VL_ASSIGNBIT_WI(0, bit+3, datap, (digit&8)>>3);
          VL_ASSIGNBIT_WI(0, bit+2, datap, (digit&4)>>2);
          VL_ASSIGNBIT_WI(0, bit+1, datap, (digit&2)>>1);
          VL_ASSIGNBIT_WI(0, bit,   datap, (digit));
          bit += 4;
      }
    }
  }
}
