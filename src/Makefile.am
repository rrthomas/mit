# Source Makefile.am
#
# (c) Mit authors 2011-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(abs_top_builddir)/lib -I$(abs_top_srcdir)/lib -I$(abs_builddir)/include -I$(abs_srcdir)/include -I$(abs_srcdir)/features $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(abs_top_srcdir)/python:$(abs_top_srcdir)/src:$(abs_top_builddir)/src:$(abs_top_srcdir)/src/specializer:$(abs_top_builddir)/src/specializer:$(abs_top_srcdir)/src/features:$(abs_top_builddir)/src/features; $(PYTHON)

lib_LTLIBRARIES = libmit.la
C_SRCS = constants.c stack.c args.c
nodist_LIB_SRCS = include/mit/registers.h include/mit/opcodes.h instructions.c
pkgdata_DATA = spec.yaml
LIB_CORE_SRCS = \
	autonumber.py \
	instruction.py \
	stack.py \
	spec.py \
	code_util.py \
	instruction_gen.py \
	params.py.in
nodist_libmit_la_SOURCES = $(C_SRCS) $(nodist_LIB_SRCS)
libmit_la_LIBADD = $(top_builddir)/lib/libgnu.la
libmit_la_LDFLAGS = -no-undefined -export-symbols-regex '^mit_.*'

bin_PROGRAMS = mit@PACKAGE_SUFFIX@$(EXEEXT)
MIT_BINARY = $(abs_builddir)/mit@PACKAGE_SUFFIX@$(EXEEXT)
man_MANS = mit@PACKAGE_SUFFIX@.1
mit@PACKAGE_SUFFIX@_LDADD = libmit.la $(top_builddir)/lib/libgnu.la
nodist_mit@PACKAGE_SUFFIX@_SOURCES = main.c
mit@PACKAGE_SUFFIX@_SOURCES = warn.c warn.h
nodist_pkginclude_HEADERS = include/mit/opcodes.h include/mit/registers.h
pkginclude_HEADERS = include/mit/mit.h
noinst_HEADERS = run.h

warn.c $(C_SRCS) specializer.c instructions.c main.c: include/mit/registers.h include/mit/opcodes.h

.c.s:
	$(COMPILE) -c -S -o $@ $<

spec.yaml: gen-yaml-spec spec.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-yaml-spec > spec.yaml || ( rm -f spec.yaml; exit 1 )

include/mit/mit.h: $(top_builddir)/config.status include/mit/mit.h.in include/mit/registers.h include/mit/opcodes.h
	cd $(top_builddir) && $(SHELL) ./config.status $(subdir)/$@

# Depend on mit@PACKAGE_SUFFIX@$(EXEEXT) rather than explicitly make-ing it, as otherwise
# we break parallel builds, as libmit.la can be built twice in parallel,
# which can fail. Set distcleancheck_listfiles below to fix distcheck.
mit@PACKAGE_SUFFIX@.1: mit@PACKAGE_SUFFIX@$(EXEEXT) $(top_builddir)/build-aux/man-include.man mit-include.man
## Exit gracefully if mit.1 is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--name="Virtual machine" \
		--include=$(top_builddir)/build-aux/man-include.man \
		--include=$(builddir)/mit-include.man \
		--output=$@ $(MIT_BINARY); \
	fi

include/mit:
	cd include && if test ! -e mit@PACKAGE_SUFFIX@; then $(LN_S) mit mit@PACKAGE_SUFFIX@; fi

include/mit/registers.h: gen-registers spec.py
	$(MKDIR_P) include/mit
	$(PYTHON_WITH_PATH) $(srcdir)/gen-registers > include/mit/registers.h || ( rm -f include/mit/registers.h; exit 1 )

include/mit/opcodes.h: gen-opcodes spec.py instruction.py
	$(MKDIR_P) include/mit
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes > include/mit/opcodes.h || ( rm -f include/mit/opcodes.h; exit 1 )

instructions.c: gen-instructions spec.py instruction.py stack.py code_util.py instruction_gen.py
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
	    $(C_SRCS) \
	    $(pkginclude_HEADERS) \
	    $(LIB_CORE_SRCS) \
	    gen-registers gen-opcodes gen-instructions gen-main gen-yaml-spec
	for file in $(pkginclude_HEADERS); do \
	    test -f $$file.in.bak && mv $$file.in.bak $$file.in || true; \
	done

EXTRA_DIST = \
	$(LIB_CORE_SRCS) \
	$(C_SRCS) \
	gen-registers \
	gen-opcodes \
	gen-instructions \
	gen-main \
	gen-yaml-spec \
	mit-include.man.in

DISTCLEANLOCALDIRS = __pycache__
distclean-local:
	rm -rf $(DISTCLEANLOCALDIRS)

DISTCLEANFILES = mit@PACKAGE_SUFFIX@.1 \
	$(nodist_LIB_SRCS) \
	$(pkgdata_DATA) \
	$(nodist_mit@PACKAGE_SUFFIX@_SOURCES) \
	include/mit
# Ignore built files that are part of the distribution (specifically,
# mit.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'

# Features
# lib_LTLIBRARIES += libmitfeatures.la
# libmitfeatures_la_SOURCES =
# nodist_libmitfeatures_la_SOURCES =
# libmitfeatures_la_LIBADD = libmit.la $(top_builddir)/lib/libgnu.la
# libmitfeatures_la_LDFLAGS = -no-undefined -export-symbols-regex '^mit_.*'

$(libmitfeatures_la_SOURCES): include/mit/mit.h

include features/features.am
include specializer/specializer.am
