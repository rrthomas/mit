# Python bindings Makefile.am
#
# (c) Mit authors 2019-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

PYTHON_ENVIRONMENT = export PYTHONPATH=$(abs_top_srcdir)/python:$(abs_top_srcdir)/src:$(abs_top_builddir)/src:$(abs_top_srcdir)/src/features;

bin_SCRIPTS = mit@PACKAGE_SUFFIX@-dump mit@PACKAGE_SUFFIX@-shell
man_MANS = mit@PACKAGE_SUFFIX@-dump.1 mit@PACKAGE_SUFFIX@-shell.1
mit_pkgpythondir = $(pkgpythondir)@PACKAGE_SUFFIX@
mit_pkgpython_PYTHON =				\
	mit/__init__.py				\
	mit/ctypes_align.py			\
	mit/int128.py				\
	mit/autonumber.py			\
	mit/extra_errors.py			\
	mit/globals.py				\
	mit/ipython_suppress_traceback.py	\
	mit/state.py				\
	mit/assembler.py
nodist_mit_pkgpython_PYTHON = mit/binding.py mit/enums.py mit/extra_enums.py

install_edit = sed \
	-e 's|@pkgdatadir[@]|'`$(CYGPATH_W) $(pkgdatadir)`'|g'

inplace_edit = sed \
	-e 's|@pkgdatadir[@]|$(top_srcdir)/src/mit_core|g'

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

mit/binding.py: $(top_builddir)/config.status mit/binding.py.in
	cd $(top_builddir) && $(SHELL) ./config.status $(subdir)/$@

mit/enums.py: $(top_srcdir)/src/mit_core/mit_spec.yaml Makefile mit/enums.py.in
	@rm -f $@ $@.tmp
	$(AM_V_GEN)$(inplace_edit) $(srcdir)/'$@.in' >$@.tmp
	$(AM_V_at)mv $@.tmp $@

mit/extra_enums.py: gen-extra-enums $(top_srcdir)/src/features/extra_instructions.py
	$(PYTHON_ENVIRONMENT) $(PYTHON) $(srcdir)/gen-extra-enums > mit/extra_enums.py || ( rm -f mit/extra_enums.py; exit 1 )

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
mit@PACKAGE_SUFFIX@-dump: mit-dump
	cp mit-dump $@
	chmod +x $@

mit@PACKAGE_SUFFIX@-shell: mit-shell
	cp mit-shell $@
	chmod +x $@

mit@PACKAGE_SUFFIX@-dump.1: mit-dump.1
	cp mit-dump.1 $@

mit@PACKAGE_SUFFIX@-shell.1: mit-shell.1
	cp mit-shell.1 $@
endif

EXTRA_DIST = \
	gen-extra-enums			\
	mit-dump-include.man.in		\
	mit-shell-include.man.in	\
	$(man_MANS)			\
	mit/binding.py.in		\
	mit/enums.py.in			\
	mit-dump.in			\
	mit-shell.in

DISTCLEANFILES = $(bin_SCRIPTS) $(man_MANS) mit/enums.py
