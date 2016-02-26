
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "vpi_user.h"
#include "sv_vpi_user.h"

#define MAXLINE 4096
#define MAXWIDTH 10
#define MAXARGS 64
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

static int rpipe;
static int wpipe;

static vpiHandle from_myhdl_systf_handle = NULL;
static vpiHandle to_myhdl_systf_handle = NULL;

static char changeFlag[MAXARGS];

static char bufcp[MAXLINE];

static myhdl_time64_t myhdl_time;
static myhdl_time64_t verilog_time;
static myhdl_time64_t pli_time;
static int delta;

/* prototypes */
static PLI_INT32 from_myhdl_calltf(PLI_BYTE8 *user_data);
static PLI_INT32 to_myhdl_calltf(PLI_BYTE8 *user_data);
static PLI_INT32 readonly_callback(p_cb_data cb_data);
static PLI_INT32 delay_callback(p_cb_data cb_data);
static PLI_INT32 delta_callback(p_cb_data cb_data);
static PLI_INT32 change_callback(p_cb_data cb_data);

static int init_pipes();

static myhdl_time64_t timestruct_to_time(const struct t_vpi_time*ts);

/* from Icarus */
static myhdl_time64_t timestruct_to_time(const struct t_vpi_time*ts)
{
      myhdl_time64_t ti = ts->high;
      ti <<= 32;
      ti += ts->low & 0xffffffff;
      return ti;
}

static int init_pipes()
{
  char *w;
  char *r;

  static int init_pipes_flag = 0;

  if (init_pipes_flag) {
    return(0);
  }

  if ((w = getenv("MYHDL_TO_PIPE")) == NULL) {
    vpi_printf("ERROR: no write pipe to myhdl\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  if ((r = getenv("MYHDL_FROM_PIPE")) == NULL) {
    vpi_printf("ERROR: no read pipe from myhdl\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  wpipe = atoi(w);
  rpipe = atoi(r);
  init_pipes_flag = 1;
  return (0);
}

static PLI_INT32 from_myhdl_calltf(PLI_BYTE8 *user_data)
{
  vpiHandle reg_iter, reg_handle;
  s_vpi_time verilog_time_s;
  char buf[MAXLINE];
  char s[MAXWIDTH];
  int n;

  static int from_myhdl_flag = 0;

  if (from_myhdl_flag) {
    vpi_printf("ERROR: $from_myhdl called more than once\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  from_myhdl_flag = 1;

  init_pipes();

  verilog_time_s.type = vpiSimTime;
  vpi_get_time(NULL, &verilog_time_s);
  verilog_time = timestruct_to_time(&verilog_time_s);
  if (verilog_time != 0) {
    vpi_printf("ERROR: $from_myhdl should be called at time 0\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  sprintf(buf, "FROM 0 ");
  pli_time = 0;
  delta = 0;

  from_myhdl_systf_handle = vpi_handle(vpiSysTfCall, NULL);
  reg_iter = vpi_iterate(vpiArgument, from_myhdl_systf_handle);
  while ((reg_handle = vpi_scan(reg_iter)) != NULL) {
    if (vpi_get(vpiType, reg_handle) != vpiReg) {
      vpi_printf("ERROR: $from_myhdl argument %s should be a reg\n",
                vpi_get_str(vpiName, reg_handle));
      vpi_control(vpiFinish, 1);  /* abort simulation */
      return(0);
    }
    strcat(buf, vpi_get_str(vpiName, reg_handle));
    strcat(buf, " ");
    sprintf(s, "%d ", vpi_get(vpiSize, reg_handle));
    strcat(buf, s);
    vpi_free_object(reg_handle);
  }
  //vpi_free_object(reg_iter);

  n = write(wpipe, buf, strlen(buf));

  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("Info: MyHDL simulator down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  assert(n > 0);
  buf[n] = '\0';

  return(0);
}

static PLI_INT32 to_myhdl_calltf(PLI_BYTE8 *user_data)
{
  vpiHandle net_iter, net_handle, cb_h;
  char buf[MAXLINE];
  char s[MAXWIDTH];
  int n;
  int i;
  int *id;
  s_cb_data cb_data_s;
  s_vpi_time verilog_time_s;
  s_vpi_time time_s;
  s_vpi_value value_s;
  static int to_myhdl_flag = 0;

  if (to_myhdl_flag) {
    vpi_printf("ERROR: $to_myhdl called more than once\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  to_myhdl_flag = 1;

  init_pipes();

  verilog_time_s.type = vpiSimTime;
  vpi_get_time(NULL, &verilog_time_s);
  verilog_time = timestruct_to_time(&verilog_time_s);
  if (verilog_time != 0) {
    vpi_printf("ERROR: $to_myhdl should be called at time 0\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  sprintf(buf, "TO 0 ");
  pli_time = 0;
  delta = 0;

  time_s.type = vpiSuppressTime;
  value_s.format = vpiSuppressVal;
  cb_data_s.reason = cbValueChange;
  cb_data_s.cb_rtn = change_callback;
  cb_data_s.time = &time_s;
  cb_data_s.value = &value_s;
  // value_s.format = vpiHexStrVal;
  i = 0;
  to_myhdl_systf_handle = vpi_handle(vpiSysTfCall, NULL);
  net_iter = vpi_iterate(vpiArgument, to_myhdl_systf_handle);
  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    if (i == MAXARGS) {
      vpi_printf("ERROR: $to_myhdl max #args (%d) exceeded\n", MAXARGS);
      vpi_control(vpiFinish, 1);  /* abort simulation */
    }
    strcat(buf, vpi_get_str(vpiName, net_handle));
    strcat(buf, " ");
    sprintf(s, "%d ", vpi_get(vpiSize, net_handle));
    strcat(buf, s);
    changeFlag[i] = 0;
    id = malloc(sizeof(int));
    *id = i;
    cb_data_s.user_data = (PLI_BYTE8 *)id;
    cb_data_s.obj = net_handle;
    cb_h = vpi_register_cb(&cb_data_s);
    vpi_free_object(cb_h);
    i++;
    vpi_free_object(net_handle);
  }
  //vpi_free_object(net_iter);

  n = write(wpipe, buf, strlen(buf));

  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("ABORT from $to_myhdl\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';
  assert(n > 0);

  // register read-only callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadOnlySynch;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = readonly_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  cb_h = vpi_register_cb(&cb_data_s);
  vpi_free_object(cb_h);

  // pre-register delta cycle callback //
  delta = 0;
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 1;
  cb_data_s.reason = cbAfterDelay;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = delta_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  cb_h = vpi_register_cb(&cb_data_s);
  vpi_free_object(cb_h);

  return(0);
}


static PLI_INT32 readonly_callback(p_cb_data cb_data)
{
  vpiHandle net_iter, net_handle, cb_h;
  s_cb_data cb_data_s;
  s_vpi_time verilog_time_s;
  s_vpi_value value_s;
  s_vpi_time time_s;
  char buf[MAXLINE];
  int n;
  int i;
  char *myhdl_time_string;
  myhdl_time64_t delay;

  static int start_flag = 1;

  if (start_flag) {
    start_flag = 0;
    n = write(wpipe, "START", 5);
    // vpi_printf("INFO: RO cb at start-up\n");
    if ((n = read(rpipe, buf, MAXLINE)) == 0) {
      vpi_printf("ABORT from RO cb at start-up\n");
      vpi_control(vpiFinish, 1);  /* abort simulation */
    }
    assert(n > 0);
  }

  buf[0] = '\0';
  verilog_time_s.type = vpiSimTime;
  vpi_get_time(NULL, &verilog_time_s);
  verilog_time = timestruct_to_time(&verilog_time_s);
   if (verilog_time != (pli_time * 1000 + delta)) {
     vpi_printf("%u %u\n", verilog_time_s.high, verilog_time_s.low );
     vpi_printf("%llu %llu %d\n", verilog_time, pli_time, delta);
   }
  /* Icarus 0.7 fails on this assertion beyond 32 bits due to a bug */
  // assert(verilog_time == pli_time * 1000 + delta);
  assert( (verilog_time & 0xFFFFFFFF) == ( (pli_time * 1000 + delta) & 0xFFFFFFFF ) );
  sprintf(buf, "%llu ", pli_time);
  net_iter = vpi_iterate(vpiArgument, to_myhdl_systf_handle);
  value_s.format = vpiHexStrVal;
  i = 0;
  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    if (changeFlag[i]) {
      strcat(buf, vpi_get_str(vpiName, net_handle));
      strcat(buf, " ");
      vpi_get_value(net_handle, &value_s);
      strcat(buf, value_s.value.str);
      strcat(buf, " ");
      changeFlag[i] = 0;
    }
    i++;
    vpi_free_object(net_handle);  // done with this one
  }
  //vpi_free_object(net_iter);

  n = write(wpipe, buf, strlen(buf));
  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    // vpi_printf("ABORT from RO cb\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  assert(n > 0);
  buf[n] = '\0';



  /* save copy for later callback */
  strcpy(bufcp, buf);

  myhdl_time_string = strtok(buf, " ");
  myhdl_time = (myhdl_time64_t) strtoull(myhdl_time_string, (char **) NULL, 10);
  delay = (myhdl_time - pli_time) * 1000;
  assert(delay >= 0);
  assert(delay <= 0xFFFFFFFF);
  if (delay > 0) { // schedule cbAfterDelay callback
    assert(delay > delta);
    delay -= delta;
    /* Icarus 20030518 runs RO callbacks when time has already advanced */
    /* Therefore, one had to compensate for the prescheduled delta callback */
    /* delay -= 1; */
    /* Icarus 20031009 has a different scheduler, more correct I believe */
    /* compensation is no longer necessary */
    delta = 0;
    pli_time = myhdl_time;

    // register cbAfterDelay callback //
    time_s.type = vpiSimTime;
    time_s.high = 0;
    time_s.low = (PLI_UINT32) delay;
    cb_data_s.reason = cbAfterDelay;
    cb_data_s.user_data = NULL;
    cb_data_s.cb_rtn = delay_callback;
    cb_data_s.obj = NULL;
    cb_data_s.time = &time_s;
    cb_data_s.value = NULL;
    cb_h = vpi_register_cb(&cb_data_s);
    vpi_free_object(cb_h);
  } else {
    delta++;
    assert(delta < 1000);
  }
  return(0);
}

static PLI_INT32 delay_callback(p_cb_data cb_data)
{
  s_vpi_time time_s;
  s_cb_data cb_data_s;
  vpiHandle cb_h;

  // register readonly callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadOnlySynch;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = readonly_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  cb_h = vpi_register_cb(&cb_data_s);
  vpi_free_object(cb_h);

  // register delta callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 1;
  cb_data_s.reason = cbAfterDelay;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = delta_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  cb_h = vpi_register_cb(&cb_data_s);
  vpi_free_object(cb_h);

  return(0);
}

static PLI_INT32 delta_callback(p_cb_data cb_data)
{
  s_cb_data cb_data_s;
  s_vpi_time time_s;
  vpiHandle reg_iter, reg_handle, cb_h;
  s_vpi_value value_s;

  if (delta == 0) {
    return(0);
  }

  /* skip time value */
  strtok(bufcp, " ");

  reg_iter = vpi_iterate(vpiArgument, from_myhdl_systf_handle);

  value_s.format = vpiHexStrVal;
  while ((value_s.value.str = strtok(NULL, " ")) != NULL) {
    reg_handle = vpi_scan(reg_iter);
    vpi_put_value(reg_handle, &value_s, NULL, vpiNoDelay);
    vpi_free_object(reg_handle);
  }

  if (reg_iter != NULL) {
    vpi_free_object(reg_iter);
  }

  // register readonly callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadOnlySynch;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = readonly_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  cb_h = vpi_register_cb(&cb_data_s);
  vpi_free_object(cb_h);

  // register delta callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 1;
  cb_data_s.reason = cbAfterDelay;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = delta_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  cb_h = vpi_register_cb(&cb_data_s);
  vpi_free_object(cb_h);

  return(0);
}

static PLI_INT32 change_callback(p_cb_data cb_data)
{
  int *id;

  // vpi_printf("change callback");
  id = (int *)cb_data->user_data;
  changeFlag[*id] = 1;
  return(0);
}


void myhdl_register()
{
  s_vpi_systf_data tf_data;

  tf_data.type      = vpiSysTask;
  tf_data.tfname    = "$to_myhdl";
  tf_data.calltf    = (void *) to_myhdl_calltf;
  tf_data.compiletf = NULL;
  tf_data.sizetf    = NULL;
  tf_data.user_data = "$to_myhdl";
  vpi_register_systf(&tf_data);
  //vpi_free_object(tf_data);               // @mod cfelton

  tf_data.type      = vpiSysTask;
  tf_data.tfname    = "$from_myhdl";
  tf_data.calltf    = (void *) from_myhdl_calltf;
  tf_data.compiletf = NULL;
  tf_data.sizetf    = NULL;
  tf_data.user_data = "$from_myhdl";
  vpi_register_systf(&tf_data);
  //vpi_free_object(tf_data);               // @mod cfelton
}

void (*vlog_startup_routines[])() = {
      myhdl_register,
      0
};

/* dummy +loadvpi= boostrap routine - mimics old style exec all routines */
/* in standard PLI vlog_startup_routines table */
void vpi_compat_bootstrap(void)
{
 int i;

 for (i = 0;; i++)
  {
   if (vlog_startup_routines[i] == NULL) break;
   vlog_startup_routines[i]();
  }
}
