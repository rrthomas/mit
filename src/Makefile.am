# Source Makefile.am
#
# (c) Reuben Thomas 2011-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib $(WARN_CFLAGS)

lib_LTLIBRARIES = libsmite.la
libsmite_la_SOURCES = bits_util.c storage.c instruction.c step.c run.c debug.c object.c \
	register-list.h instruction-list.h instruction-type-list.h instruction-actions.h
libsmite_la_LIBADD = $(top_builddir)/lib/libgnu.la

bin_PROGRAMS = smite
bin_SCRIPTS = @PACKAGE@-dump
# FIXME: install as smite-shell; add man page
noinst_SCRIPTS = @PACKAGE@.py
man_MANS = @PACKAGE@.1 @PACKAGE@-dump.1
pkgdata_DATA = completions
smite_LDADD = lib@PACKAGE@.la $(top_builddir)/lib/libgnu.la
smite_SOURCES = main.c tbl_opts.h register-list.h $(internal_HDRS)
internal_HDRS = public.h aux.h debug.h opcodes.h opcodes-extra.h
include_HEADERS = @PACKAGE@.h @PACKAGE@_aux.h @PACKAGE@_debug.h @PACKAGE@_opcodes.h

completions: register-list.h tbl_commands.h
	$(CPP) -I$(srcdir) $(srcdir)/completions.h | grep -v "^#" > $@

bits_util.lo debug.lo instruction.lo object.lo run.lo step.lo storage.lo main.o: external-syms.h
step.lo: instruction-actions.h
bits_util.lo debug.lo instruction.lo object.lo step.lo storage.lo main.o: register-list.h instruction-list.h instruction-type-list.h
main.o: tbl_opts.h register-list.h

# Depend on @PACKAGE@$(EXEEXT) rather than explicitly make-ing it, as otherwise
# we break parallel builds, as lib@PACKAGE@.la can be built twice in parallel,
# which can fail. Set distcleancheck_listfiles below to fix distcheck.
@PACKAGE@.1: @PACKAGE@$(EXEEXT)
## Exit gracefully if @PACKAGE@.1 is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--name="Virtual machine" \
		--output=$@ ./@PACKAGE@$(EXEEXT); \
	fi

# N.B. PACKAGE_UPPER is not enclosed in @, so it can be used in C
# identifiers.
do_subst = sed -e 's,[@]pkgdatadir[@],$(pkgdatadir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]PACKAGE_NAME[@],$(PACKAGE_NAME),g' \
	-e 's,PACKAGE_UPPER,$(PACKAGE_UPPER),g'

@PACKAGE@_opcodes.h: opcodes.h Makefile
	$(do_subst) < $(srcdir)/opcodes.h > $@

@PACKAGE@.h: public.h external-syms.txt external-defines.txt Makefile
	$(do_subst) < $(srcdir)/public.h > $@.tmp
	cat external-syms.txt external-defines.txt | $(top_srcdir)/build-aux/add-symbol-prefix $@.tmp > $@
	rm $@.tmp

@PACKAGE@_aux.h: aux.h external-syms.txt external-defines.txt Makefile
	$(do_subst) < $(srcdir)/aux.h > $@.tmp
	cat external-syms.txt external-defines.txt | $(top_srcdir)/build-aux/add-symbol-prefix $@.tmp > $@
	rm $@.tmp

@PACKAGE@_debug.h: debug.h external-syms.txt external-defines.txt Makefile
	$(do_subst) < $(srcdir)/debug.h > $@.tmp
	cat external-syms.txt external-defines.txt | $(top_srcdir)/build-aux/add-symbol-prefix $@.tmp > $@
	rm $@.tmp

external-defines.txt: $(internal_HDRS)
	$(top_srcdir)/build-aux/find-external-defines $(srcdir) > $@

register-list.h: gen-register-list vm_data.py
	$(PYTHON) $(srcdir)/gen-register-list > register-list.h

opcodes-extra.h: gen-opcodes-extra opcodes_extra.py
	$(PYTHON) $(srcdir)/gen-opcodes-extra > opcodes-extra.h

instruction-list.h: gen-instruction-list vm_data.py
	$(PYTHON) $(srcdir)/gen-instruction-list > instruction-list.h

instruction-type-list.h: gen-instruction-type-list vm_data.py
	$(PYTHON) $(srcdir)/gen-instruction-type-list > instruction-type-list.h

instruction-actions.h: gen-actions vm_data.py
	$(PYTHON) $(srcdir)/gen-actions > instruction-actions.h

# Actually needs .o files, but since find-external-syms requires GNU tools,
# don't force remaking external-syms.txt; instead, add it to EXTRA_DIST.
# find-external-syms takes care of remaking the executable.
# The target depends on $(internal_HDRS), but with .in files instead of .h
# N.B. find-external-syms runs make! This can cause duplicate compilation.
external-syms.txt: $(lib@PACKAGE@_la_sources) public.h.in aux.h debug.h opcodes.h
	$(top_srcdir)/build-aux/find-external-syms $(PACKAGE) $(srcdir) > $@

external-syms.h: external-syms.txt
	sed -e 's/\(.*\)/#define \1 $(PACKAGE)_\1/' < $^ > $@

@PACKAGE@-dump: @PACKAGE@-dump.in Makefile
	$(do_subst) < $(srcdir)/@PACKAGE@-dump.in > $@
	chmod +x $@

CLOC = cloc --force-lang="C",h

loc:
	$(CLOC) $(lib@PACKAGE@_la_SOURCES) $(@PACKAGE@_SOURCES) \
	vm_data.py opcodes_extra.py gen-register-list gen-instruction-list gen-instruction-type-list gen-opcodes-extra gen-actions @PACKAGE@.py

EXTRA_DIST = \
	@PACKAGE@-dump.in @PACKAGE@-dump.1 \
	completions.h public.h.in \
	external-syms.txt external-syms.h \
	vm_data.py opcodes_extra.py \
	@PACKAGE@.py \
	gen-register-list gen-instruction-list gen-instruction-type-list gen-actions gen-opcodes-extra

DISTCLEANFILES = @PACKAGE@-dump @PACKAGE@.1 @PACKAGE-dump.1 completions $(include_HEADERS) external-defines.txt external-syms.txt external-syms.h
# Ignore built files that are part of the distribution (specifically,
# @PACKAGE@.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'
