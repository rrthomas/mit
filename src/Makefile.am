# Source Makefile.am
#
# (c) Reuben Thomas 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AM_CPPFLAGS = -I$(top_builddir)/lib -I$(top_srcdir)/lib $(WARN_CFLAGS)
PYTHON_WITH_PATH = export PYTHONPATH=$(top_srcdir)/python:$(top_builddir)/src; $(PYTHON)

lib_LTLIBRARIES = libsmite.la
C_SRCS = storage.c extra.h object.c
GENERATED_SRCS = registers.h opcodes-core.h opcodes-extra.h instructions.c extra.c
SMITE_CORE_SRCS = smite_core/vm_data.py smite_core/vm_data_extra.py smite_core/instruction_gen.py
libsmite_la_SOURCES = $(C_SRCS) $(GENERATED_SRCS)
libsmite_la_LIBADD = $(top_builddir)/lib/libgnu.la

bin_PROGRAMS = smite
man_MANS = @PACKAGE@.1
smite_LDADD = lib@PACKAGE@.la $(top_builddir)/lib/libgnu.la
smite_SOURCES = main.c tbl_opts.h
pkginclude_HEADERS = @PACKAGE@.h opcodes.h opcodes-extra.h

step.lo: instructions.c
object.lo step.lo storage.lo main.o: registers.h opcodes-core.h opcodes-extra.h
main.o: tbl_opts.h registers.h

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
	$(PYTHON_WITH_PATH) $(srcdir)/gen-registers > registers.h

opcodes-extra.h: gen-opcodes-extra smite_core/vm_data_extra.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes-extra > opcodes-extra.h

opcodes-core.h: gen-opcodes-core smite_core/vm_data.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-opcodes-core > opcodes-core.h

instructions.c: gen-instructions smite_core/vm_data.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-instructions > instructions.c

# Note: we grep config.log because the generated header file has the symbols
# sorted lexically, and we need the output in the same order as the input.
smite_core/type_sizes.py: $(top_builddir)/configure gen-type-sizes collate-type-sizes registers.h smite_core/vm_data_extra.py smite_core/instruction_gen.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-type-sizes > type-sizes.ac && \
	autoconf type-sizes.ac > type-sizes && \
	CONFIG_SITE= CPPFLAGS="-I$(builddir) -I$(srcdir) -I$(top_builddir) $(AM_CPPFLAGS)" $(SHELL) type-sizes && \
	$(MKDIR_P) smite_core && \
	$(GREP) "^#define SIZEOF" config.log | cut -d " " -f 3 | \
		( $(PYTHON_WITH_PATH) $(srcdir)/collate-type-sizes > smite_core/type_sizes.py )

extra.c: gen-extra smite_core/vm_data_extra.py smite_core/instruction_gen.py smite_core/type_sizes.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-extra > extra.c || rm -f extra.c

loc:
	$(SLOCCOUNT) \
		$(C_SRCS) \
		$(@PACKAGE@_SOURCES) \
		$(SMITE_CORE_SRCS) \
		gen-registers gen-opcodes-core gen-opcodes-extra gen-instructions gen-extra

EXTRA_DIST = \
	@PACKAGE@.h.in \
	$(SMITE_CORE_SRCS) \
	gen-registers \
	gen-opcodes-core \
	gen-opcodes-extra \
	gen-instructions \
	gen-extra \
	gen-type-sizes \
	collate-type-sizes

distclean-local:
	rm -rf autom4te.cache smite_core/__pycache__

DISTCLEANFILES = @PACKAGE@.1 extra.c type-sizes.ac type-sizes config.log smite_core/type_sizes.py
# Ignore built files that are part of the distribution (specifically,
# @PACKAGE@.1)
distcleancheck_listfiles = \
       find . -type f -exec sh -c 'test -f $(srcdir)/$$1 || echo $$1' \
	    sh '{}' ';'
