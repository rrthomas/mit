# Source Makefile.am
#
# (c) Mit authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib -I$(builddir)/include -I$(srcdir)/include $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(top_srcdir)/python:$(top_srcdir)/src:$(top_builddir)/src; $(PYTHON)

lib_LTLIBRARIES = lib@PACKAGE@@PACKAGE_SUFFIX@.la
C_SRCS = storage.c object.c
nodist_LIB_SRCS = include/@PACKAGE@/registers.h include/@PACKAGE@/opcodes.h include/@PACKAGE@/ext-opcodes.h instructions.c ext.c
LIB_CORE_SRCS = mit_core/instruction.py mit_core/vm_data.py mit_core/ext.py mit_core/instruction_gen.py
nodist_lib@PACKAGE@@PACKAGE_SUFFIX@_la_SOURCES = $(C_SRCS) $(nodist_LIB_SRCS)
lib@PACKAGE@@PACKAGE_SUFFIX@_la_LIBADD = $(top_builddir)/lib/libgnu.la
lib@PACKAGE@@PACKAGE_SUFFIX@_la_LDFLAGS = -no-undefined -export-symbols-regex '^mit_.*'

bin_PROGRAMS = @PACKAGE@@PACKAGE_SUFFIX@$(EXEEXT)
man_MANS = @PACKAGE@@PACKAGE_SUFFIX@.1
@PACKAGE@@PACKAGE_SUFFIX@_LDADD = lib@PACKAGE@@PACKAGE_SUFFIX@.la $(top_builddir)/lib/libgnu.la
nodist_@PACKAGE@@PACKAGE_SUFFIX@_SOURCES = main.c
mit_pkgincludedir = $(pkgincludedir)@PACKAGE_SUFFIX@
nodist_mit_pkginclude_HEADERS = include/@PACKAGE@/opcodes.h include/@PACKAGE@/ext-opcodes.h include/@PACKAGE@/registers.h
mit_pkginclude_HEADERS = include/@PACKAGE@/@PACKAGE@.h

step.lo: instructions.c
object.lo step.lo storage.lo main.o: include/@PACKAGE@/registers.h include/@PACKAGE@/opcodes.h include/@PACKAGE@/ext-opcodes.h
main.o: main.c include/@PACKAGE@/registers.h

.c.s:
	$(COMPILE) -c -S $<

include/@PACKAGE@/@PACKAGE@.h: $(top_builddir)/config.status $(srcdir)/include/@PACKAGE@/@PACKAGE@.h.in
	cd $(top_builddir) && $(SHELL) ./config.status $(subdir)/$@

# Depend on @PACKAGE@@PACKAGE_SUFFIX@$(EXEEXT) rather than explicitly make-ing it, as otherwise
# we break parallel builds, as lib@PACKAGE@@PACKAGE_SUFFIX@.la can be built twice in parallel,
# which can fail. Set distcleancheck_listfiles below to fix distcheck.
@PACKAGE@@PACKAGE_SUFFIX@.1: @PACKAGE@@PACKAGE_SUFFIX@$(EXEEXT) @PACKAGE@-include.man
## Exit gracefully if @PACKAGE@.1 is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--name="Virtual machine" \
		--include=@PACKAGE@-include.man \
		--output=$@ ./@PACKAGE@@PACKAGE_SUFFIX@$(EXEEXT); \
	fi

include/@PACKAGE@/registers.h: include/@PACKAGE@@PACKAGE_SUFFIX@

include/@PACKAGE@@PACKAGE_SUFFIX@:
	cd include && if test ! -e @PACKAGE@@PACKAGE_SUFFIX@; then $(LN_S) @PACKAGE@ @PACKAGE@@PACKAGE_SUFFIX@; fi

include/@PACKAGE@/registers.h: gen-registers mit_core/vm_data.py mit_core/instruction.py
	$(MKDIR_P) include/@PACKAGE@
	$(PYTHON_WITH_PATH) $(srcdir)/gen-registers > include/@PACKAGE@/registers.h || ( rm -f include/@PACKAGE@/registers.h; exit 1 )

include/@PACKAGE@/ext-opcodes.h: gen-ext-opcodes mit_core/ext.py mit_core/instruction.py
	$(MKDIR_P) include/@PACKAGE@
	$(PYTHON_WITH_PATH) $(srcdir)/gen-ext-opcodes > include/@PACKAGE@/ext-opcodes.h || ( rm -f include/@PACKAGE@/ext-opcodes.h; exit 1 )

include/@PACKAGE@/opcodes.h: gen-opcodes mit_core/vm_data.py mit_core/instruction.py
	$(MKDIR_P) include/@PACKAGE@
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes > include/@PACKAGE@/opcodes.h || ( rm -f include/@PACKAGE@/opcodes.h; exit 1 )

instructions.c: gen-instructions mit_core/vm_data.py mit_core/instruction.py mit_core/instruction_gen.py mit_core/type_sizes.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instructions > instructions.c || ( rm -f instructions.c; exit 1 )

# Note: we grep config.log because the generated header file has the symbols
# sorted lexically, and we need the output in the same order as the input.
mit_core/type_sizes.py: $(top_builddir)/config.status gen-type-sizes collate-type-sizes include/@PACKAGE@/registers.h mit_core/ext.py mit_core/instruction.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-type-sizes > type-sizes.ac && \
	autoconf type-sizes.ac > type-sizes && \
	CONFIG_SITE= CC="$(CC)" CPPFLAGS="$(CPPFLAGS) -I$(builddir) -I$(srcdir) -I$(top_builddir) $(AM_CPPFLAGS)" $(SHELL) type-sizes && \
	$(MKDIR_P) mit_core && \
	$(GREP) "^#define SIZEOF" config.log | cut -d " " -f 3 | \
		( $(PYTHON_WITH_PATH) $(srcdir)/collate-type-sizes > mit_core/type_sizes.py ) || ( rm -f type-sizes.ac type-sizes mit_core/type_sizes.py; exit 1 )

ext.c: gen-ext mit_core/ext.py mit_core/instruction.py mit_core/instruction_gen.py mit_core/type_sizes.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-ext > ext.c || ( rm -f ext.c; exit 1 )

main.c: $(srcdir)/feature/*/feature.py gen-main
	$(PYTHON_WITH_PATH) $(srcdir)/gen-main $(srcdir)/feature > main.c || ( rm -f main.c; exit 1 )

loc:
	$(SLOCCOUNT) \
		$(C_SRCS) \
		$(@PACKAGE@_SOURCES) \
		$(LIB_CORE_SRCS) \
		gen-registers gen-opcodes gen-ext-opcodes gen-instructions gen-ext gen-main

EXTRA_DIST = \
	$(LIB_CORE_SRCS) \
	$(C_SRCS) \
	gen-registers \
	gen-opcodes \
	gen-instructions \
	gen-main \
	gen-ext-opcodes \
	gen-ext \
	gen-type-sizes \
	collate-type-sizes

distclean-local:
	rm -rf autom4te.cache mit_core/__pycache__

DISTCLEANFILES = @PACKAGE@@PACKAGE_SUFFIX@.1 \
	$(nodist_LIB_SRCS) \
	$(nodist_@PACKAGE@@PACKAGE_SUFFIX@_SOURCES) \
	include/@PACKAGE@@PACKAGE_SUFFIX@ \
	type-sizes.ac type-sizes config.log mit_core/type_sizes.py
# Ignore built files that are part of the distribution (specifically,
# @PACKAGE@.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'

# Include feature makefile fragments
include $(srcdir)/feature/features.am
