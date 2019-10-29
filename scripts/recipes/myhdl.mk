MYHDL_UPSTREAM = $(HOME)/src/myhdl/myhdl-upgrade

all: install

$(MYHDL_UPSTREAM):
	[ -e $(dir $@) ] || install -d $(dir $@)
	cd $(dir $@) && \
	git clone https://github.com/hackfin/myhdl $(notdir $@)

install: $(MYHDL_UPSTREAM)
	cd $< && python setup.py install --user

test:
	cd $(MYHDL_UPSTREAM)/myhdl/test/conversion && $(MAKE) all


.PHONY: install test
