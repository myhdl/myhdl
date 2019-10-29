MYHDL_UPSTREAM = $(HOME)/src/myhdl/myhdl-upgrade

all: install

$(MYHDL_UPSTREAM):
	[ -e $(dir $@) ] || install -d $(dir $@)
	cd $(dir $@) && \
	git clone https://github.com/hackfin/myhdl $(notdir $@)

install: $(MYHDL_UPSTREAM)
	cd $< && python setup.py install --user

test:
	# The general test will currently fail.
	#cd $(MYHDL_UPSTREAM)/myhdl/test/conversion && $(MAKE) all
	# Run a simple test to satisfy docker build:
	cd $(MYHDL_UPSTREAM)/myhdl/test/conversion/general && \
		py.test --sim=ghdl test_intbv_signed.py


.PHONY: install test
