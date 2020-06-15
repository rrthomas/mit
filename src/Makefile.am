# Source Makefile.am
#
# (c) Mit authors 2011-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(abs_top_builddir)/lib -I$(abs_top_srcdir)/lib -I$(abs_builddir)/include -I$(abs_srcdir)/include -I$(abs_srcdir)/features $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(abs_top_srcdir)/src:$(abs_top_builddir)/src:$(abs_top_srcdir)/src/specializer:$(abs_top_builddir)/src/specializer:$(abs_top_srcdir)/src/features:$(abs_top_builddir)/src/features; $(PYTHON)

# Source files that should be distributed that Automake won't otherwise find
DIST_SRCS = \
	autonumber.py \
	action.py \
	stack.py \
	spec.py \
	code_util.py \
	run_fn.py \
	gen-opcodes \
	gen-instructions \
	gen-main \
	gen-yaml-spec

# libmit
lib_LTLIBRARIES = libmit.la
pkgdata_DATA = spec.yaml
libmit_la_SOURCES = args.c
nodist_libmit_la_SOURCES = instructions.c
libmit_la_LIBADD = $(top_builddir)/lib/libgnu.la
libmit_la_LDFLAGS = -no-undefined -export-symbols-regex '^mit_.*'
nodist_pkginclude_HEADERS = include/mit/opcodes.h include/mit/mit.h
pkginclude_HEADERS =
noinst_HEADERS = run.h

# mit binary
bin_PROGRAMS = mit@PACKAGE_SUFFIX@$(EXEEXT)
MIT_BINARY = $(abs_builddir)/mit@PACKAGE_SUFFIX@$(EXEEXT)
man_MANS = mit@PACKAGE_SUFFIX@.1
mit@PACKAGE_SUFFIX@_LDADD = libmit.la $(top_builddir)/lib/libgnu.la
nodist_mit@PACKAGE_SUFFIX@_SOURCES = main.c
mit@PACKAGE_SUFFIX@_SOURCES = warn.c warn.h

# Dependencies on auto-generated sources
# Auto-generation of dependencies does not work in this case.
warn.o constants.lo stack.lo args.lo main.o: include/mit/opcodes.h
instructions.lo main.o: main.c

.c.s:
	$(COMPILE) -c -S -o $@ $<

spec.yaml: gen-yaml-spec spec.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-yaml-spec > spec.yaml || ( rm -f spec.yaml; exit 1 )

# The man page depends on the binary because it is built by running the binary.
mit@PACKAGE_SUFFIX@.1: mit@PACKAGE_SUFFIX@$(EXEEXT) $(top_builddir)/build-aux/man-include.man mit-include.man
## Exit gracefully if mit.1 is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--name="Virtual machine" \
		--include=$(top_builddir)/build-aux/man-include.man \
		--include=$(builddir)/mit-include.man \
		--output=$@ $(MIT_BINARY); \
	fi

include/mit/opcodes.h: gen-opcodes spec.py action.py
	$(MKDIR_P) include/mit
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes > include/mit/opcodes.h || ( rm -f include/mit/opcodes.h; exit 1 )

instructions.c: gen-instructions spec.py action.py stack.py code_util.py run_fn.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instructions > instructions.c || ( rm -f instructions.c; exit 1 )

main.c: gen-main
	$(PYTHON_WITH_PATH) $(srcdir)/gen-main > main.c || ( rm -f main.c; exit 1 )

# sloccount --autogen doesn't work (Debian bug #929000), so temporarily move
# *.h.in during count.
loc:
	for file in $(pkginclude_HEADERS); do \
	    test -f $$file.in && mv $$file.in $$file.in.bak || true; \
	done && \
	$(SLOCCOUNT) --autogen \
	    $(libmit_la_SOURCES) \
	    $(pkginclude_HEADERS) \
	    $(DIST_SRCS)
	for file in $(pkginclude_HEADERS); do \
	    test -f $$file.in.bak && mv $$file.in.bak $$file.in || true; \
	done

EXTRA_DIST = \
	$(DIST_SRCS) \
	mit-include.man.in

DISTCLEANLOCALDIRS = __pycache__
distclean-local:
	rm -rf $(DISTCLEANLOCALDIRS)

DISTCLEANFILES = mit@PACKAGE_SUFFIX@.1 \
	$(nodist_libmit_la_SOURCES) \
	$(pkgdata_DATA) \
	$(nodist_mit@PACKAGE_SUFFIX@_SOURCES) \
	include/mit/opcodes.h

include features/features.am
#include specializer/specializer.am
