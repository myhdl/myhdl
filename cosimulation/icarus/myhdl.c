#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include "vpi_user.h"

#define MAXLINE 4096
#define MAXWIDTH 10

typedef int PLI_INT32;
typedef char PLI_BYTE8;

static int rpipe;
static int wpipe;

static vpiHandle from_myhdl_systf_handle = NULL;

typedef struct to_myhdl_data {
  vpiHandle systf_handle;
  short int sync_flag;
} s_to_myhdl_data, *p_to_myhdl_data;

/* prototypes */
static PLI_INT32 from_myhdl_calltf(PLI_BYTE8 *user_data);
static PLI_INT32 to_myhdl_calltf(PLI_BYTE8 *user_data);
static PLI_INT32 to_myhdl_sensitivity_callback(p_cb_data cb_data);
static PLI_INT32 to_myhdl_write_callback(p_cb_data cb_data);

static int init_pipes();

static int init_pipes()
{
  char *w;
  char *r;

  static int init_pipes_flag = 0;

  if (init_pipes_flag) {
    vprintf("INFO: pipes already initialized\n");
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

  static int from_myhdl_flag = 0;

  if (from_myhdl_flag) {
    vpi_printf("ERROR: $from_myhdl called more than once\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  from_myhdl_flag = 1;

  init_pipes();

  vpi_printf("Hello from $from_myhdl %d %d\n", rpipe, wpipe);
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
    vpi_printf("Info: myhdl down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';
  return(0);


}

static PLI_INT32 to_myhdl_calltf(PLI_BYTE8 *user_data)
{
  vpiHandle systf_handle, net_iter, net_handle;
  vpiHandle cb_h;
  char buf[MAXLINE];
  char s[MAXWIDTH];
  int n;
  s_vpi_time current_time;
  s_cb_data cb_data_s;
  s_vpi_time time_s;
  s_vpi_value value_s;
  p_to_myhdl_data to_myhdl_data;
  static int to_myhdl_flag = 0;

  if (to_myhdl_flag) {
    vpi_printf("ERROR: $to_myhdl called more than once\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  to_myhdl_flag = 1;

  init_pipes();

  vpi_printf("Hello from $to_myhdl %d %d\n", rpipe, wpipe);
  systf_handle = vpi_handle(vpiSysTfCall, NULL);

  to_myhdl_data = (p_to_myhdl_data)malloc(sizeof(s_to_myhdl_data));
  to_myhdl_data->systf_handle = systf_handle;
  to_myhdl_data->sync_flag = 0;
 
  /* setup sensitivity callback */
  time_s.type = vpiSuppressTime;
  value_s.format = vpiSuppressVal;
  cb_data_s.reason = cbValueChange;
  cb_data_s.user_data = (PLI_BYTE8 *)to_myhdl_data;
  cb_data_s.cb_rtn = to_myhdl_sensitivity_callback;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;

  net_iter = vpi_iterate(vpiArgument, systf_handle);

  current_time.type = vpiSimTime;
  vpi_get_time(NULL, &current_time);
  sprintf(buf, "TO %x%08x ", current_time.high, current_time.low);

  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    cb_data_s.obj = net_handle;
    vpi_register_cb(&cb_data_s);
    strcat(buf, vpi_get_str(vpiName, net_handle));
    strcat(buf, " ");
    sprintf(s, "%d ", vpi_get(vpiSize, net_handle));
    strcat(buf, s);
  }
  write(wpipe, buf, strlen(buf));

  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("Info: myhdl down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';

  // register write callback by default at time 0 //
  vpi_printf("register cb\n");
  to_myhdl_data->sync_flag = 1;
  time_s.type = vpiSimTime;
  time_s.high = 0;
  time_s.low = 0;
  cb_data_s.reason = cbReadWriteSynch;
  cb_data_s.user_data = (PLI_BYTE8 *)to_myhdl_data;
  cb_data_s.cb_rtn = to_myhdl_write_callback;
  cb_data_s.obj = NULL;
  cb_data_s.time = &time_s;
  cb_data_s.value = NULL;
  vpi_register_cb(&cb_data_s);

  return(0);

}


static PLI_INT32 to_myhdl_sensitivity_callback(p_cb_data cb_data)
{
  vpiHandle cb_h;
  s_cb_data cb_data_s;
  s_vpi_time time_s;
  p_to_myhdl_data to_myhdl_data;
  vpiHandle net_handle;

  to_myhdl_data = (p_to_myhdl_data)cb_data->user_data;
  vpi_printf("sens triggered\n");
  if (!to_myhdl_data->sync_flag) {
    vpi_printf("register cb\n");
    to_myhdl_data->sync_flag = 1;
    time_s.type = vpiSimTime;
    time_s.high = 0;
    time_s.low = 0;
    cb_data_s.reason = cbReadWriteSynch;
    cb_data_s.user_data = (PLI_BYTE8 *)to_myhdl_data;
    cb_data_s.cb_rtn = to_myhdl_write_callback;
    cb_data_s.obj = NULL;
    cb_data_s.time = &time_s;
    cb_data_s.value = NULL;
    vpi_register_cb(&cb_data_s);
  }
  return(0);
}

static PLI_INT32 to_myhdl_write_callback(p_cb_data cb_data)
{
  vpiHandle systf_handle;
  vpiHandle net_iter, net_handle;
  vpiHandle reg_iter, reg_handle;
  p_to_myhdl_data to_myhdl_data;
  s_vpi_time current_time;
  s_vpi_value value_s;
  char buf[MAXLINE];
  int n;

  static int start_flag = 1;

  vpi_printf("write callback\n");

  if (start_flag) {
    start_flag = 0;
    write(wpipe, "START", 5);
    if ((n = read(rpipe, buf, MAXLINE)) == 0) {
      vpi_printf("Info: myhdl down\n");
      vpi_control(vpiFinish, 1);  /* abort simulation */
      buf[n] = '\0';
    }
  }

  to_myhdl_data = (p_to_myhdl_data)cb_data->user_data;
  vpi_printf("sync flag: %d\n", to_myhdl_data->sync_flag);
  to_myhdl_data->sync_flag = 0;
  systf_handle = to_myhdl_data->systf_handle;

  net_iter = vpi_iterate(vpiArgument, systf_handle);
  buf[0] = '\0';
  current_time.type = vpiSimTime;
  vpi_get_time(systf_handle, &current_time);
  sprintf(buf, "%x%08x ", current_time.high, current_time.low);
  value_s.format = vpiHexStrVal;
  while ((net_handle = vpi_scan(net_iter)) != NULL) {
    vpi_get_value(net_handle, &value_s);
    strcat(buf, value_s.value.str);
    strcat(buf, " ");
  }
  write(wpipe, buf, strlen(buf));
  if ((n = read(rpipe, buf, MAXLINE)) == 0) {
    vpi_printf("Info: myhdl down\n");
    vpi_control(vpiFinish, 1);  /* abort simulation */
    return(0);
  }
  buf[n] = '\0';
  vpi_printf("C Read %d %s\n", n, buf);
  reg_iter = vpi_iterate(vpiArgument, from_myhdl_systf_handle);
  while ((reg_handle = vpi_scan(reg_iter)) != NULL) {
    assert(sscanf(buf, "%s", value_s.value.str));
    vpi_put_value(reg_handle, &value_s, NULL, vpiNoDelay);
  }

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
