# Source Makefile.am
#
# (c) Reuben Thomas 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(top_srcdir)/python; $(PYTHON)

lib_LTLIBRARIES = libsmite.la
C_SRCS = bits_util.c storage.c instruction.c extra.h object.c
GENERATED_SRCS = register-list.h instruction-list.h instruction-type-list.h actions.c extra.c
SMITE_CORE_SRCS = smite_core/vm_data.py smite_core/vm_data_extra.py smite_core/action_gen.py smite_core/events.py
libsmite_la_SOURCES = $(C_SRCS) $(GENERATED_SRCS)
libsmite_la_LIBADD = $(top_builddir)/lib/libgnu.la

bin_PROGRAMS = smite
man_MANS = @PACKAGE@.1
smite_LDADD = lib@PACKAGE@.la $(top_builddir)/lib/libgnu.la
smite_SOURCES = main.c tbl_opts.h
pkginclude_HEADERS = @PACKAGE@.h aux.h opcodes.h opcodes-extra.h

step.lo: actions.c
bits_util.lo instruction.lo object.lo step.lo storage.lo main.o: register-list.h instruction-list.h instruction-type-list.h opcodes-extra.h
main.o: tbl_opts.h register-list.h

# Depend on @PACKAGE@$(EXEEXT) rather than explicitly make-ing it, as otherwise
# we break parallel builds, as lib@PACKAGE@.la can be built twice in parallel,
# which can fail. Set distcleancheck_listfiles below to fix distcheck.
@PACKAGE@.1: @PACKAGE@$(EXEEXT) @PACKAGE@-include.man
## Exit gracefully if @PACKAGE@.1 is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--name="Virtual machine" \
		--include=@PACKAGE@-include.man \
		--output=$@ ./@PACKAGE@$(EXEEXT); \
	fi

actions.predictor_pickle: actions.trace smite_core/events.py gen-predictor
	$(PYTHON_WITH_PATH) $(srcdir)/gen-predictor actions.trace $@

actions.labels_pickle: actions.predictor_pickle smite_core/events.py gen-labels
	$(PYTHON_WITH_PATH) $(srcdir)/gen-labels actions.predictor_pickle $@

register-list.h: gen-register-list smite_core/vm_data.py smite_core/action_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-register-list > register-list.h

opcodes-extra.h: gen-opcodes-extra smite_core/vm_data_extra.py smite_core/action_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes-extra > opcodes-extra.h

instruction-list.h: gen-instruction-list smite_core/vm_data.py smite_core/action_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instruction-list > instruction-list.h

instruction-type-list.h: gen-instruction-type-list smite_core/vm_data.py smite_core/action_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instruction-type-list > instruction-type-list.h

actions.c: gen-actions smite_core/events.py smite_core/vm_data.py actions.labels_pickle smite_core/action_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-actions actions.labels_pickle > actions.c

extra.c: gen-extra smite_core/vm_data_extra.py smite_core/action_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-extra > extra.c

loc:
	$(SLOCCOUNT) \
		$(C_SRCS) \
		$(@PACKAGE@_SOURCES) \
		$(SMITE_CORE_SRCS) \
		gen-register-list gen-instruction-list gen-instruction-type-list gen-opcodes-extra gen-actions

EXTRA_DIST = \
	@PACKAGE@.h.in \
	$(SMITE_CORE_SRCS) \
	gen-register-list gen-instruction-list gen-instruction-type-list gen-actions gen-opcodes-extra gen-extra \
	actions.trace

DISTCLEANFILES = @PACKAGE@.1
# Ignore built files that are part of the distribution (specifically,
# @PACKAGE@.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'
