#include "Python.h"

#include <assert.h>
#include <stdio.h>

static PyObject *_simulator;
static PyObject *_siglist;
static PyObject *_futureEvents;
static PyObject *_WaiterList;
static PyObject *_Waiter;
static PyObject *Signal;
static PyObject *delay;
static PyObject *StopSimulation;
static PyObject *SuspendSimulation;


PyObject *
run(PyObject *self, PyObject *args, PyObject *kwargs)
{

    PyObject *sim;
    long int duration = 0;
    int quiet = 0;
    static char *argnames[] = {"sim", "duration", "quiet", NULL};

    PyObject *waiters, *waiter, *clauses, *clone, *clause;
    PyObject *type, *newtO, *event, *id;
    PyObject *actives, *values;
    long long int maxTime = -1;
    long long int t = 0;
    long long int ct = 0;
    long long int newt = 0;
    int nr;
    int len, i, j;
    PyObject *tO, *extl, *s, *hr, *hgl, *nt, *c, *wl, *ev, *ctO, *r, *it;



    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|li", argnames, 
				     &sim, &duration, &quiet)) {
	return NULL;
    }
    waiters = PyObject_GetAttrString(sim, "_waiters");
    tO = PyObject_GetAttrString(_simulator, "_time");
    t = PyLong_AsLongLong(tO);
    Py_DECREF(tO);
    actives = PyDict_New();

    for (;;) {

	len = PyList_Size(_siglist);
	for (i = 0; i < len; i++) {
	    s = PyList_GetItem(_siglist, i);
	    extl = PyObject_CallMethod(s, "_update", NULL);
	    for (j = 0; j < PyList_Size(extl) ; j++) {
		PyList_Append(waiters, PyList_GetItem(extl, j));
	    }
	    Py_DECREF(extl);
	}
	PySequence_DelSlice(_siglist, 0, len);

	while (PyList_Size(waiters) > 0) {
	    waiter = PyList_GetItem(waiters, 0);
	    Py_INCREF(waiter);
	    PySequence_DelItem(waiters, 0);
	    hr = PyObject_GetAttrString(waiter, "hasRun");
	    if (PyObject_IsTrue(hr)) {
		Py_DECREF(waiter);
		Py_DECREF(hr);
		continue;
	    }
	    Py_DECREF(hr);
	    hgl = PyObject_CallMethod(waiter, "hasGreenLight", NULL);
	    if (!PyObject_IsTrue(hgl)) {
		Py_DECREF(waiter);
		Py_DECREF(hgl);
		continue;
	    }
	    Py_DECREF(hgl);
	    nt = PyObject_CallMethod(waiter, "next", NULL);
	    if (nt == NULL) {
		if (PyErr_ExceptionMatches(PyExc_StopIteration)) {
		    c = PyObject_GetAttrString(waiter, "caller");
		    if (c != Py_None) {
			PyList_Append(waiters, c);	  
		    }
		    Py_DECREF(waiter);
		    Py_DECREF(c);
		    continue;
		} else {
		    Py_DECREF(waiter);
		    goto exception;
		}
	    }
	    Py_DECREF(waiter);
	    clauses = PyTuple_GetItem(nt, 0);
	    clone = PyTuple_GetItem(nt, 1);
	    nr = PyTuple_Size(clauses);
	    for (i = 0; i < nr; i++) {
		clause = PySequence_GetItem(clauses, i);
		type = PyObject_Type(clause);
		if (type == _WaiterList) {
		    // PyObject_Print(clause, stdout, 0);
		    PyList_Append(clause, clone);
		    if (nr > 1) {
			id = PyLong_FromVoidPtr(clause);
			PyDict_SetItem(actives, id, clause);
			Py_DECREF(id);
		    }
		} else if (PyObject_IsInstance(clause, Signal)) {
		    wl = PyObject_GetAttrString(clause, "_eventWaiters");
		    PyList_Append(wl, clone);
		    if (nr > 1) {
			id = PyLong_FromVoidPtr(wl);
			PyDict_SetItem(actives, id, wl);
			Py_DECREF(id);
		    }
		    Py_DECREF(wl);
		} else if (type == delay) {
		    ctO = PyObject_GetAttrString(clause, "_time");
		    ct = PyLong_AsLongLong(ctO);
		    Py_DECREF(ctO);
		    ev = PyTuple_New(2);
		    newtO = PyLong_FromLongLong(t + ct);
		    PyTuple_SetItem(ev, 0, newtO);
		    Py_INCREF(clone);
		    PyTuple_SetItem(ev, 1, clone);
		    PyList_Append(_futureEvents, ev);
		    Py_DECREF(ev);
		} else {
		    assert(0);
		}
		// Py_DECREF(clone);
		Py_DECREF(type);
		Py_DECREF(clause);
	    }
	    Py_DECREF(nt);
	}


	if (PyList_Size(_siglist) > 0) {
	    continue;
	}

	if (PyDict_Size(actives) > 0) {
	    values = PyDict_Values(actives);
	    for (i = 0; i < PyList_Size(values); i++) {
		wl = PyList_GetItem(values, i);
		r = PyObject_CallMethod(wl, "purge", NULL);
		Py_DECREF(r);
	    }
	    Py_DECREF(values);
	    PyDict_Clear(actives);
	}
	// PyObject_Print(actives, stdout, 0);

	if (PyList_Size(_futureEvents) > 0) {
	    r = PyObject_CallMethod(_futureEvents, "sort", NULL);
	    Py_DECREF(r);
	    newtO = PyTuple_GetItem(PyList_GetItem(_futureEvents, 0), 0);
	    PyObject_SetAttrString(_simulator, "_time", newtO);
	    t = PyLong_AsLongLong(newtO);
	    while (PyList_Size(_futureEvents) > 0) {
		ev = PyList_GetItem(_futureEvents, 0);
		newtO = PyTuple_GetItem(ev, 0);
		newt = PyLong_AsLongLong(newtO);
		event = PyTuple_GetItem(ev, 1);
		if (newt == t) {
		    type = PyObject_Type(event);
		    if (type == _Waiter) {
			PyList_Append(waiters, event);
		    } else {
			extl = PyObject_CallMethod(event, "apply", NULL);
			for (j = 0; j < PyList_Size(extl); j++) {
			    PyList_Append(waiters, PyList_GetItem(extl, j));
			}
			Py_DECREF(extl);
		    }
		    Py_DECREF(type);
		    PySequence_DelItem(_futureEvents, 0);
		} else {
		    break;
		}
	    }

	} else {
	    PyErr_SetString(StopSimulation, "No more events");
	    printf("No more events\n");
	    goto exception;
	}
    }

    assert(0); /* should not get here */

 exception:
    if (PyErr_ExceptionMatches(StopSimulation)) {
	printf("Stop simulation reached \n");
	PyErr_Clear();
	r = PyObject_CallMethod(sim, "_finalize", NULL);
	Py_DECREF(r);
	Py_DECREF(actives);
	Py_DECREF(waiters);
	return PyInt_FromLong(0);
    }
    Py_DECREF(actives);
    Py_DECREF(waiters);
    return Py_BuildValue("");
}


static PyMethodDef simruncmethods[] = {
    {"run", (PyCFunction)run, METH_VARARGS | METH_KEYWORDS},
    {NULL, NULL, 0, NULL}
};

void initsimrunc(void) {
    PyObject *SignalModule;
    PyObject *delayModule;
    PyObject *_WaiterModule;
    PyObject *utilModule;

    Py_InitModule("simrunc", simruncmethods);

    _simulator = PyImport_ImportModule("_simulator");
    _siglist = PyObject_GetAttrString(_simulator, "_siglist");
    _futureEvents = PyObject_GetAttrString(_simulator, "_futureEvents");
    SignalModule = PyImport_ImportModule("Signal");
    Signal = PyObject_GetAttrString(SignalModule, "Signal");
    _WaiterList = PyObject_GetAttrString(SignalModule, "_WaiterList");
    delayModule = PyImport_ImportModule("delay");
    delay = PyObject_GetAttrString(delayModule, "delay");
    _WaiterModule = PyImport_ImportModule("_Waiter");
    _Waiter = PyObject_GetAttrString(_WaiterModule, "_Waiter");
    utilModule = PyImport_ImportModule("util");
    StopSimulation = PyObject_GetAttrString(utilModule, "StopSimulation");
    SuspendSimulation = PyObject_GetAttrString(utilModule, "SuspendSimulation");

    Py_DECREF(SignalModule);
    Py_DECREF(delayModule);
    Py_DECREF(_WaiterModule);
    Py_DECREF(utilModule);
}
