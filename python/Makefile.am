# Python bindings Makefile.am
#
# (c) Mit authors 2019-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

PYTHON_ENVIRONMENT = export PYTHONPATH=$(abs_top_srcdir)/python:$(abs_top_srcdir)/src:$(abs_top_builddir)/src:$(abs_top_srcdir)/src/features;

bin_SCRIPTS = mit@PACKAGE_SUFFIX@-shell
man_MANS = mit@PACKAGE_SUFFIX@-shell.1
mit_pkgpythondir = $(pkgpythondir)
mit_pkgpython_PYTHON =				\
	mit/__init__.py				\
	mit/autonumber.py			\
	mit/globals.py				\
	mit/ipython_suppress_traceback.py	\
	mit/memory.py				\
	mit/state.py				\
	mit/assembler.py
nodist_mit_pkgpython_PYTHON = mit/binding.py mit/enums.py mit/trap_enums.py

install_edit = sed \
	-e 's|@pkgdatadir[@]|'`$(CYGPATH_M) $(pkgdatadir)`'|g'

inplace_edit = sed \
	-e 's|@pkgdatadir[@]|'`$(CYGPATH_M) $(abs_top_builddir)/src`'|g'

all-local: $(nodist_mit_pkgpython_PYTHON)

%.1: % %-include.man $(top_builddir)/build-aux/man-include.man
## Exit gracefully if $@ is not writeable, such as during distcheck!
	$(AM_V_GEN)if ( touch $@.w && rm -f $@.w; ) >/dev/null 2>&1; then \
	  $(PYTHON_ENVIRONMENT) $(top_srcdir)/build-aux/missing --run $(HELP2MAN) --no-info \
		--no-discard-stderr \
		--include=$(builddir)/$*-include.man \
		--include=$(top_builddir)/build-aux/man-include.man \
		--output=$@ ./$*; \
	fi

mit/enums.py: $(top_builddir)/src/spec.yaml Makefile mit/enums.py.in
	@$(MKDIR_P) mit
	@rm -f $@ $@.tmp
	$(AM_V_GEN)$(inplace_edit) $(srcdir)/'$@.in' >$@.tmp
	$(AM_V_at)mv $@.tmp $@

mit/trap_enums.py: gen-trap-enums $(top_srcdir)/src/features/traps.py
	@$(MKDIR_P) mit
	$(PYTHON_ENVIRONMENT) $(PYTHON) $(srcdir)/gen-trap-enums > mit/trap_enums.py || ( rm -f mit/trap_enums.py; exit 1 )

install-data-hook: mit/enums.py
	@$(install_edit) $(top_srcdir)/python/mit/enums.py.in > enums.py.tmp
	@echo $(INSTALL_SCRIPT) -m 644 enums.py.tmp $(DESTDIR)$(mit_pkgpythondir)/enums.py
	@$(INSTALL_SCRIPT) -m 644 enums.py.tmp $(DESTDIR)$(mit_pkgpythondir)/enums.py
	@rm -f enums.py.tmp

# sloccount --autogen doesn't work (Debian bug #929000), so temporarily move
# *.py.in during count.
loc:
	for file in $(nodist_mit_pkgpython_PYTHON); do \
		test -f $$file.in && mv $$file.in $$file.in.bak || true; \
	done && \
	$(SLOCCOUNT) --autogen $(bin_SCRIPTS) $(mit_pkgpython_PYTHON) $(nodist_mit_pkgpython_PYTHON); \
	for file in $(nodist_mit_pkgpython_PYTHON); do \
		test -f $$file.in.bak && mv $$file.in.bak $$file.in || true; \
	done

if USING_PACKAGE_SUFFIX
mit@PACKAGE_SUFFIX@-shell: mit-shell
	cp mit-shell $@
	chmod +x $@

mit@PACKAGE_SUFFIX@-shell.1: mit-shell.1
	cp mit-shell.1 $@
endif

EXTRA_DIST = \
	gen-trap-enums			\
	mit-shell-include.man.in	\
	$(man_MANS)			\
	mit/binding.py			\
	mit/enums.py.in			\
	mit-profile.in			\
	mit-shell.in

DISTCLEANFILES = $(bin_SCRIPTS) $(man_MANS) mit/enums.py
