PYTEST_OPTS ?= -W error::DeprecationWarning -W error::pytest.PytestWarning

install:
	python setup.py install

localinstall:
	python setup.py install --home=${HOME}

docs:
	tox -e docs html

livedocs:
	tox -e docs livehtml

release:
	- rm MANIFEST 
	- rm CHANGELOG.txt
	hg glog > CHANGELOG.txt
	python setup.py sdist 

core:
	pytest ./myhdl/test/core ${PYTEST_OPTS}

iverilog_myhdl.vpi:
	${MAKE} -C cosimulation/icarus myhdl.vpi

iverilog_cosim: iverilog_myhdl.vpi
	${MAKE} -C cosimulation/icarus test

iverilog_general:
	pytest ./myhdl/test/conversion/general --sim iverilog ${PYTEST_OPTS}

iverilog_toverilog: iverilog_myhdl.vpi
	pytest ./myhdl/test/conversion/toVerilog --sim iverilog ${PYTEST_OPTS}

iverilog_bugs:
	pytest ./myhdl/test/bugs --sim iverilog ${PYTEST_OPTS}

iverilog: iverilog_cosim
	pytest ./myhdl/test/conversion/general ./myhdl/test/conversion/toVerilog ./myhdl/test/bugs --sim iverilog ${PYTEST_OPTS}

ghdl_general:
	pytest ./myhdl/test/conversion/general --sim ghdl ${PYTEST_OPTS}

ghdl_tovhdl:
	pytest ./myhdl/test/conversion/toVHDL --sim ghdl ${PYTEST_OPTS}

ghdl_bugs:
	pytest ./myhdl/test/bugs --sim ghdl ${PYTEST_OPTS}

ghdl:
	pytest ./myhdl/test/conversion/general ./myhdl/test/conversion/toVHDL ./myhdl/test/bugs --sim ghdl ${PYTEST_OPTS}

test: core iverilog ghdl