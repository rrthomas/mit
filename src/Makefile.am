# Source Makefile.am
#
# (c) SMite authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(top_srcdir)/python:$(top_builddir)/src; $(PYTHON)

lib_LTLIBRARIES = libsmite.la
C_SRCS = storage.c object.c
nodist_LIB_SRCS = registers.h opcodes.h ext-opcodes.h instructions.c ext.c
LIB_CORE_SRCS = smite_core/vm_data.py smite_core/ext.py smite_core/instruction_gen.py
nodist_libsmite_la_SOURCES = $(C_SRCS) $(nodist_LIB_SRCS)
libsmite_la_LIBADD = $(top_builddir)/lib/libgnu.la
libsmite_la_LDFLAGS = -no-undefined -export-symbols-regex '^smite_.*'

bin_PROGRAMS = smite$(EXEEXT)
man_MANS = @PACKAGE@.1
smite_LDADD = lib@PACKAGE@.la $(top_builddir)/lib/libgnu.la
nodist_smite_SOURCES = main.c
nodist_pkginclude_HEADERS = opcodes.h ext-opcodes.h
pkginclude_HEADERS = @PACKAGE@.h

step.lo: instructions.c
object.lo step.lo storage.lo main.o: registers.h opcodes.h ext-opcodes.h
main.o: gen-main registers.h

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

registers.h: gen-registers smite_core/vm_data.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-registers > registers.h || ( rm -f registers.h; exit 1 )

ext-opcodes.h: gen-ext-opcodes smite_core/ext.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-ext-opcodes > ext-opcodes.h || ( rm -f ext-opcodes.h; exit 1 )

opcodes.h: gen-opcodes smite_core/vm_data.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes > opcodes.h || ( rm -f opcodes.h; exit 1 )

instructions.c: gen-instructions smite_core/vm_data.py smite_core/instruction_gen.py smite_core/type_sizes.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instructions > instructions.c || ( rm -f instructions.c; exit 1 )

# Note: we grep config.log because the generated header file has the symbols
# sorted lexically, and we need the output in the same order as the input.
smite_core/type_sizes.py: $(top_builddir)/config.status gen-type-sizes collate-type-sizes registers.h smite_core/ext.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-type-sizes > type-sizes.ac && \
	autoconf type-sizes.ac > type-sizes && \
	CONFIG_SITE= CPPFLAGS="$(CPPFLAGS) -I$(builddir) -I$(srcdir) -I$(top_builddir) $(AM_CPPFLAGS)" $(SHELL) type-sizes && \
	$(MKDIR_P) smite_core && \
	$(GREP) "^#define SIZEOF" config.log | cut -d " " -f 3 | \
		( $(PYTHON_WITH_PATH) $(srcdir)/collate-type-sizes > smite_core/type_sizes.py ) || ( rm -f type-sizes.ac type-sizes smite_core/type_sizes.py; exit 1 )

ext.c: gen-ext smite_core/ext.py smite_core/instruction_gen.py smite_core/type_sizes.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-ext > ext.c || ( rm -f ext.c; exit 1 )

main.c: $(srcdir)/feature/*.py gen-main
	$(PYTHON_WITH_PATH) $(builddir)/gen-main $(srcdir)/feature > main.c || ( rm -f main.c; exit 1 )

loc:
	$(SLOCCOUNT) \
		$(C_SRCS) \
		$(@PACKAGE@_SOURCES) \
		$(LIB_CORE_SRCS) \
		gen-registers gen-opcodes gen-ext-opcodes gen-instructions gen-ext gen-main.in

EXTRA_DIST = \
	$(LIB_CORE_SRCS) \
	$(C_SRCS) \
	gen-registers \
	gen-opcodes \
	gen-instructions \
	gen-main.in \
	gen-ext-opcodes \
	gen-ext \
	gen-type-sizes \
	collate-type-sizes \
	$(srcdir)/feature/*.py

distclean-local:
	rm -rf autom4te.cache smite_core/__pycache__

DISTCLEANFILES = @PACKAGE@.1 \
	$(nodist_LIB_SRCS) \
	$(nodist_smite_SOURCES) \
	type-sizes.ac type-sizes config.log smite_core/type_sizes.py
# Ignore built files that are part of the distribution (specifically,
# @PACKAGE@.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'
