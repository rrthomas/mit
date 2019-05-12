# Source Makefile.am
#
# (c) Mit authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib -I$(builddir)/include -I$(srcdir)/include -I$(builddir)/features $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(top_srcdir)/python:$(top_srcdir)/src:$(top_builddir)/src; $(PYTHON)

lib_LTLIBRARIES = libmit@PACKAGE_SUFFIX@.la
C_SRCS = storage.c object.c
nodist_LIB_SRCS = include/mit/registers.h include/mit/opcodes.h instructions.c
LIB_CORE_SRCS = mit_core/instruction.py mit_core/vm_data.py mit_core/ext.py mit_core/instruction_gen.py mit_core/c_util.py
nodist_libmit@PACKAGE_SUFFIX@_la_SOURCES = $(C_SRCS) $(nodist_LIB_SRCS)
libmit@PACKAGE_SUFFIX@_la_LIBADD = $(top_builddir)/lib/libgnu.la
libmit@PACKAGE_SUFFIX@_la_LDFLAGS = -no-undefined -export-symbols-regex '^mit_.*'

bin_PROGRAMS = mit@PACKAGE_SUFFIX@$(EXEEXT)
man_MANS = mit@PACKAGE_SUFFIX@.1
mit@PACKAGE_SUFFIX@_LDADD = libmit@PACKAGE_SUFFIX@.la libmitfeatures@PACKAGE_SUFFIX@.la $(top_builddir)/lib/libgnu.la
nodist_mit@PACKAGE_SUFFIX@_SOURCES = main.c
mit_pkgincludedir = $(pkgincludedir)@PACKAGE_SUFFIX@
nodist_mit_pkginclude_HEADERS = include/mit/opcodes.h include/mit/registers.h
mit_pkginclude_HEADERS = include/mit/mit.h

step.lo: instructions.c
object.lo step.lo storage.lo: include/mit/registers.h
object.lo step.lo storage.lo main.o: include/mit/opcodes.h
main.o: main.c include/mit/registers.h

.c.s:
	$(COMPILE) -c -S $<

include/mit/mit.h: $(top_builddir)/config.status include/mit/mit.h.in
	cd $(top_builddir) && $(SHELL) ./config.status $(subdir)/$@

# Depend on mit@PACKAGE_SUFFIX@$(EXEEXT) rather than explicitly make-ing it, as otherwise
# we break parallel builds, as libmit@PACKAGE_SUFFIX@.la can be built twice in parallel,
# which can fail. Set distcleancheck_listfiles below to fix distcheck.
mit@PACKAGE_SUFFIX@.1: mit@PACKAGE_SUFFIX@$(EXEEXT) mit-include.man
## Exit gracefully if mit.1 is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--name="Virtual machine" \
		--include=$(srcdir)/mit-include.man \
		--output=$@ ./mit@PACKAGE_SUFFIX@$(EXEEXT); \
	fi

include/mit/registers.h: include/mit@PACKAGE_SUFFIX@

include/mit@PACKAGE_SUFFIX@:
	cd include && if test ! -e mit@PACKAGE_SUFFIX@; then $(LN_S) mit mit@PACKAGE_SUFFIX@; fi

include/mit/registers.h: gen-registers mit_core/vm_data.py mit_core/instruction.py
	$(MKDIR_P) include/mit
	$(PYTHON_WITH_PATH) $(srcdir)/gen-registers > include/mit/registers.h || ( rm -f include/mit/registers.h; exit 1 )

include/mit/opcodes.h: gen-opcodes mit_core/vm_data.py mit_core/instruction.py
	$(MKDIR_P) include/mit
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes > include/mit/opcodes.h || ( rm -f include/mit/opcodes.h; exit 1 )

instructions.c: gen-instructions mit_core/vm_data.py mit_core/instruction.py mit_core/instruction_gen.py mit_core/type_sizes.py mit_core/c_util.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instructions > instructions.c || ( rm -f instructions.c; exit 1 )

# Note: we grep config.log because the generated header file has the symbols
# sorted lexically, and we need the output in the same order as the input.
mit_core/type_sizes.py: $(top_builddir)/config.status gen-type-sizes collate-type-sizes include/mit/registers.h mit_core/ext.py mit_core/instruction.py mit_core/c_util.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-type-sizes > type-sizes.ac && \
	autoconf type-sizes.ac > type-sizes && \
	CONFIG_SITE= CC="$(CC)" CPPFLAGS="$(CPPFLAGS) -I$(builddir) -I$(srcdir) -I$(top_builddir) $(AM_CPPFLAGS)" $(SHELL) type-sizes && \
	$(MKDIR_P) mit_core && \
	$(GREP) "^#define SIZEOF" config.log | cut -d " " -f 3 | \
		( $(PYTHON_WITH_PATH) $(srcdir)/collate-type-sizes > mit_core/type_sizes.py ) || ( rm -f type-sizes.ac type-sizes mit_core/type_sizes.py; exit 1 )

main.c: gen-main
	$(PYTHON_WITH_PATH) $(srcdir)/gen-main > main.c || ( rm -f main.c; exit 1 )

loc:
	$(SLOCCOUNT) \
		$(C_SRCS) \
		$(mit_SOURCES) \
		$(LIB_CORE_SRCS) \
		gen-registers gen-opcodes gen-instructions gen-main

EXTRA_DIST = \
	$(LIB_CORE_SRCS) \
	$(C_SRCS) \
	gen-registers \
	gen-opcodes \
	gen-instructions \
	gen-main \
	gen-type-sizes \
	collate-type-sizes \
	mit-include.man

distclean-local:
	rm -rf autom4te.cache mit_core/__pycache__

DISTCLEANFILES = mit@PACKAGE_SUFFIX@.1 \
	$(nodist_LIB_SRCS) \
	$(nodist_mit@PACKAGE_SUFFIX@_SOURCES) \
	include/mit@PACKAGE_SUFFIX@ \
	type-sizes.ac type-sizes config.log mit_core/type_sizes.py
# Ignore built files that are part of the distribution (specifically,
# mit.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'

# Features
include features/features.am
