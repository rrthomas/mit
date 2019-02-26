# Source Makefile.am
#
# (c) Reuben Thomas 2011-2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib $(WARN_CFLAGS)

lib_LTLIBRARIES = libsmite.la
libsmite_la_SOURCES = bits_util.c storage.c instruction.c extra.c extra.h step.c run.c object.c \
	register-list.h instruction-list.h instruction-type-list.h step-actions.h
libsmite_la_LIBADD = $(top_builddir)/lib/libgnu.la

bin_PROGRAMS = smite
man_MANS = @PACKAGE@.1
smite_LDADD = lib@PACKAGE@.la $(top_builddir)/lib/libgnu.la
smite_SOURCES = main.c tbl_opts.h $(internal_HDRS)
pkginclude_HEADERS = @PACKAGE@.h aux.h opcodes.h opcodes-extra.h

step.lo: step-actions.h
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

.trace.predictor_pickle:
	$(PYTHON) $(srcdir)/gen-predictor $< $@

.predictor_pickle.labels_pickle:
	$(PYTHON) $(srcdir)/gen-labels $< $@

register-list.h: gen-register-list vm_data.py
	$(PYTHON) $(srcdir)/gen-register-list > register-list.h

opcodes-extra.h: gen-opcodes-extra opcodes_extra.py
	$(PYTHON) $(srcdir)/gen-opcodes-extra > opcodes-extra.h

instruction-list.h: gen-instruction-list vm_data.py
	$(PYTHON) $(srcdir)/gen-instruction-list > instruction-list.h

instruction-type-list.h: gen-instruction-type-list vm_data.py
	$(PYTHON) $(srcdir)/gen-instruction-type-list > instruction-type-list.h

step-actions.h: gen-actions vm_data.py step.labels_pickle
	$(PYTHON) $(srcdir)/gen-actions step.labels_pickle > step-actions.h

loc:
	$(CLOC) $(CLOC_OPTS) \
		$(lib@PACKAGE@_la_SOURCES) \
		$(@PACKAGE@_SOURCES) \
		gen-register-list gen-instruction-list gen-instruction-type-list gen-opcodes-extra gen-actions

EXTRA_DIST = \
	@PACKAGE@.h.in \
	vm_data.py opcodes_extra.py \
	gen-register-list gen-instruction-list gen-instruction-type-list gen-actions gen-opcodes-extra

DISTCLEANFILES = @PACKAGE@.1
# Ignore built files that are part of the distribution (specifically,
# @PACKAGE@.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'
