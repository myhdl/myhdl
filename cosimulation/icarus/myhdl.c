#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include "vpi_user.h"
#include <string.h>

#define MAXLINE 4096
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

static int rpipe;
static int wpipe;

static vpiHandle from_myhdl_systf_handle = NULL;
static vpiHandle to_myhdl_systf_handle = NULL;

typedef struct cb_user_data {
  char buf[MAXLINE];
} s_cb_user_data, *p_cb_user_data;

/* prototypes */
static PLI_INT32 from_myhdl_calltf(PLI_BYTE8 *user_data);
static PLI_INT32 to_myhdl_calltf(PLI_BYTE8 *user_data);
static PLI_INT32 to_myhdl_readonly_callback(p_cb_data cb_data);
static PLI_INT32 to_myhdl_delay_callback(p_cb_data cb_data);
static PLI_INT32 to_myhdl_delta_callback(p_cb_data cb_data);

static int init_pipes();

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
  vpiHandle net_iter, net_handle;
  vpiHandle cb_h;
  s_vpi_time current_time;
  char buf[MAXLINE];
  char s[MAXWIDTH];
  int n;
  vpiHandle q;

  static int from_myhdl_flag = 0;

  if (from_myhdl_flag) {
    vpi_printf("ERROR: $from_myhdl called more than once\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  from_myhdl_flag = 1;

  init_pipes();

#ifdef DEBUG
  vpi_printf("Hello from $from_myhdl %d %d\n", rpipe, wpipe);
#endif
  from_myhdl_systf_handle = vpi_handle(vpiSysTfCall, NULL);
  net_iter = vpi_iterate(vpiArgument, from_myhdl_systf_handle);

  current_time.type = vpiSimTime;
  vpi_get_time(NULL, &current_time);
  sprintf(buf, "FROM %x%08x ", current_time.high, current_time.low);

  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    strcat(buf, vpi_get_str(vpiName, net_handle));
    strcat(buf, " ");
    sprintf(s, "%d ", vpi_get(vpiSize, net_handle));
    strcat(buf, s);
  }
  write(wpipe, buf, strlen(buf));

  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("Info: MyHDL simulator down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';

  return(0);
}

static PLI_INT32 to_myhdl_calltf(PLI_BYTE8 *user_data)
{
  vpiHandle net_iter, net_handle;
  vpiHandle cb_h;
  char buf[MAXLINE];
  char s[MAXWIDTH];
  int n;
  s_vpi_time current_time;
  s_cb_data cb_data_s;
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

#ifdef DEBUG
  vpi_printf("Hello from $to_myhdl %d %d\n", rpipe, wpipe);
#endif
  to_myhdl_systf_handle = vpi_handle(vpiSysTfCall, NULL);

  net_iter = vpi_iterate(vpiArgument, to_myhdl_systf_handle);

  current_time.type = vpiSimTime;
  vpi_get_time(NULL, &current_time);
  sprintf(buf, "TO %x%08x ", current_time.high, current_time.low);

  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    strcat(buf, vpi_get_str(vpiName, net_handle));
    strcat(buf, " ");
    sprintf(s, "%d ", vpi_get(vpiSize, net_handle));
    strcat(buf, s);
  }
  write(wpipe, buf, strlen(buf));

  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("Info: MyHDL simulator down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';

  // register read-only callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadOnlySynch;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = to_myhdl_readonly_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  vpi_register_cb(&cb_data_s);

  return(0);
}


static PLI_INT32 to_myhdl_readonly_callback(p_cb_data cb_data)
{
  vpiHandle systf_handle;
  vpiHandle net_iter, net_handle;
  vpiHandle reg_iter, reg_handle;
  s_vpi_time current_time;
  s_vpi_value value_s;
  s_cb_data cb_data_s;
  s_vpi_time time_s;
  char buf[MAXLINE];
  p_cb_user_data cb_user_data;
  char bufcp[MAXLINE];
  int n;
  char *time_high_string;
  char *time_low_string;
  PLI_UINT32 time_low;
  PLI_UINT32 time_high;
  PLI_UINT32 delay;

  static int start_flag = 1;


  if (start_flag) {
    start_flag = 0;
    write(wpipe, "START", 5);
    if ((n = read(rpipe, buf, MAXLINE)) == 0) {
      vpi_printf("Info: MyHDL simulator down\n");
      vpi_control(vpiFinish, 1);  /* abort simulation */
      buf[n] = '\0';
    }
  }

  net_iter = vpi_iterate(vpiArgument, to_myhdl_systf_handle);
  buf[0] = '\0';
  current_time.type = vpiSimTime;
  vpi_get_time(systf_handle, &current_time);
  sprintf(buf, "%xd%08x ", current_time.high, current_time.low);
  vpi_printf("%d: RW trigger\n", current_time.low);
  value_s.format = vpiHexStrVal;
  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    vpi_get_value(net_handle, &value_s);
    vpi_printf("val %s\n", value_s.value.str);
    strcat(buf, value_s.value.str);
    strcat(buf, " ");
  }
  write(wpipe, buf, strlen(buf));
  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("Info: MyHDL simulator down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';

  /* save copy for later callback */
  cb_user_data = (p_cb_user_data)malloc(sizeof(s_cb_user_data));
  strcpy(cb_user_data->buf, buf);

  time_high_string = strtok(buf, " ");
  time_low_string = strtok(NULL, " ");
  time_high = (PLI_UINT32) strtoul(time_high_string, (char **) NULL, 16);
  time_low = (PLI_UINT32) strtoul(time_low_string, (char **) NULL, 16);

  assert(time_high == current_time.high);
  if (time_low != current_time.low) { // schedule cbAfterDelay callback
    if (time_low < current_time.low) {
      delay = 0xFFFFFFFF - current_time.low + time_low;
    } else {
      delay = time_low - current_time.low;
    }
    vpi_printf("schedule delay callback\n");
    // register cbAfterDelay callback //
    time_s.type = vpiSimTime;
    time_s.high = 0;
    time_s.low = delay;
    cb_data_s.reason = cbAfterDelay;
    cb_data_s.user_data = NULL;
    cb_data_s.cb_rtn = to_myhdl_delay_callback;
    cb_data_s.obj = NULL;
    cb_data_s.time = &time_s;
    cb_data_s.value = NULL;
    vpi_register_cb(&cb_data_s);
    return(0);
  }

  /* hack: emulate cbEndOfTimeSync by cbAfterDelay */

  // register callback //
  vpi_printf("schedule delta callback\n");
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 1;
  cb_data_s.reason = cbAfterDelay;
  cb_data_s.user_data = (PLI_BYTE8 *) cb_user_data;
  cb_data_s.cb_rtn = to_myhdl_delta_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  vpi_register_cb(&cb_data_s);
  vpi_printf("scheduled delta callback\n");
  return(0);
}

static PLI_INT32 to_myhdl_delay_callback(p_cb_data cb_data)
{
  s_cb_data cb_data_s;
  s_vpi_time time_s;
  s_vpi_time current_time;
  vpi_printf("Got here delta \n");

  vpi_get_time(NULL, &current_time);
  // register readonly callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadWriteSynch;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = to_myhdl_readonly_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  vpi_register_cb(&cb_data_s);
  return(0);
}

static PLI_INT32 to_myhdl_delta_callback(p_cb_data cb_data)
{
  s_cb_data cb_data_s;
  s_vpi_time time_s;
  s_vpi_time current_time;
  p_cb_user_data cb_user_data;
  vpiHandle systf_handle;
  vpiHandle reg_iter, reg_handle;
  s_vpi_value value_s;

  vpi_printf("Got here delta \n");
  cb_user_data = (p_cb_user_data)cb_data->user_data;

  /* skip time values */
  strtok(cb_user_data->buf, " ");
  strtok(NULL, " ");

  reg_iter = vpi_iterate(vpiArgument, from_myhdl_systf_handle);

  while ((value_s.value.str = strtok(NULL, " ")) != NULL) {
    reg_handle = vpi_scan(reg_iter);
    vpi_put_value(reg_handle, &value_s, NULL, vpiNoDelay);
  }
  if (reg_iter != NULL) {
    vpi_free_object(reg_iter);
  }

  vpi_get_time(NULL, &current_time);
  // register readonly callback //
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadWriteSynch;
  cb_data_s.user_data = NULL;
  cb_data_s.cb_rtn = to_myhdl_readonly_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  vpi_register_cb(&cb_data_s);
  return(0);
}

void myhdl_register()
{
  s_vpi_systf_data tf_data;

  tf_data.type      = vpiSysTask;
  tf_data.tfname    = "$to_myhdl";
  tf_data.calltf    = to_myhdl_calltf;
  tf_data.compiletf = NULL;
  tf_data.sizetf    = NULL;
  tf_data.user_data = "$to_myhdl";
  vpi_register_systf(&tf_data);

  tf_data.type      = vpiSysTask;
  tf_data.tfname    = "$from_myhdl";
  tf_data.calltf    = from_myhdl_calltf;
  tf_data.compiletf = NULL;
  tf_data.sizetf    = NULL;
  tf_data.user_data = "$from_myhdl";
  vpi_register_systf(&tf_data);

}
