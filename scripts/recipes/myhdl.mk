MYHDL_UPSTREAM = $(HOME)/src/myhdl/myhdl-upgrade

all: install

$(MYHDL_UPSTREAM):
	[ -e $(dir $@) ] || install -d $(dir $@)
	cd $(dir $@) && \
	git clone https://github.com/hackfin/myhdl $(notdir $@)

install: $(MYHDL_UPSTREAM)
	cd $< && python setup.py install --user

TEST_LIST_TOVHDL = \
	test_slices.py \
	test_interface_vhdl.py \
	test_custom.py \
	test_enum.py \
	test_loops.py \
	test_newcustom.py \
	test_ops.py \
	test_signed.py \


TEST_LIST_GENERAL = \
	test_intbv_signed.py \
	test_ShadowSignal.py \
	test_adapter.py \
	test_bin2gray.py \
	test_case.py \
	test_class_defined_signals.py \
	test_constants.py \
	test_dec.py \
	test_errors.py \
	test_fsm.py \
	test_hec.py \
	test_inc.py \
	test_initial_values.py \
	test_intbv_signed.py \
	test_interfaces1.py \
	test_interfaces3.py \
	test_interfaces4.py \
	test_listofsigs.py \
	test_loops.py \
	test_nonlocal.py \
	test_numass.py \
	test_print.py \
	test_ram.py \
	test_randscrambler.py \
	test_rom.py \
	test_set_dir.py \
	test_ternary.py \
	test_toplevel_interfaces.py \
	test_toplevel_method.py \

TEST_TO_BE_IMPLEMENTED = \
	test_forbidden.py \

# Broken tests (unsure whether code or general sanity)
# Need to be looked at
TEST_BROKEN = \
	test_interfaces2.py \
	test_resize.py \
	test_method.py \
	test_keywords.py 


TEST_LIST = $(TEST_LIST_GENERAL:%=general/%) $(TEST_LIST_TOVHDL:%=toVHDL/%) 

# Run those tests that should pass by default:
test:
	cd $(MYHDL_UPSTREAM)/myhdl/test/conversion && \
		py.test --sim=ghdl $(TEST_LIST)

fulltest:
	# The general test will currently fail.
	cd $(MYHDL_UPSTREAM)/myhdl/test/conversion && $(MAKE) all

.PHONY: install test
