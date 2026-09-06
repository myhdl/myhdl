#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "vpi_user.h"

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

/* prototypes */
static int init_pipes();
static PLI_INT32 startofsim_callback(p_cb_data cb_data);
static PLI_INT32 readonly_callback(p_cb_data cb_data);
static PLI_INT32 delay_callback(p_cb_data cb_data);
static PLI_INT32 delta_callback(p_cb_data cb_data);
static PLI_INT32 change_callback(p_cb_data cb_data);

static int init_pipes()
{
  /* check environment variables and initialize pipes */
}

static int startofsim_callback(p_cb_data cb_data)
{
  /* init_pipes */
  /* find all input ports of the top-level module and write their names to the buffer */
  /* find all output ports of the top-level module, schedule value change callback for each of them and write their names to the buffer */
  /* register read only callback */
  /* pre-register delta cycle callback */
}

static PLI_INT32 readonly_callback(p_cb_data cb_data)
{
  /* read values of output ports that have changed (flag) and write them to the buffer */
  /* schedule cbAfterDelay callback */
}

static PLI_INT32 delay_callback(p_cb_data cb_data)
{
  /* register read only callback */
  /* register delta callback */
}

static PLI_INT32 delta_callback(p_cb_data cb_data)
{
  /* read values from the buffer and assign them to input ports */
  /* register read only callback */
  /* register delta callback */
}

static PLI_INT32 change_callback(p_cb_data cb_data)
{
  /* get the indexes of changed values and change corresponding flags */
}