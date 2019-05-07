# Python bindings Makefile.am
#
# (c) Mit authors 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

bin_SCRIPTS = mit@PACKAGE_SUFFIX@-dump mit@PACKAGE_SUFFIX@-shell
man_MANS = mit@PACKAGE_SUFFIX@-dump.1 mit@PACKAGE_SUFFIX@-shell.1
mit_pkgpythondir = $(pkgpythondir)@PACKAGE_SUFFIX@
mit_pkgpython_PYTHON =		\
	mit/__init__.py		\
	mit/__main__.py		\
	mit/assembler.py		\
	mit/vm_data.py		\
	mit/ext.py		\
	mit/instruction.py
nodist_mit_pkgpython_PYTHON = mit/binding.py

all-local: mit/binding.py

mit/binding.py: $(top_builddir)/config.status mit/binding.py.in
	cd $(top_builddir) && $(SHELL) ./config.status $(subdir)/$@


loc:
	$(SLOCCOUNT) $(bin_SCRIPTS) mit/__init__.py mit/__main__.py

if USING_PACKAGE_SUFFIX
mit@PACKAGE_SUFFIX@-dump: mit-dump
	cp mit-dump $@
	chmod +x $@

mit@PACKAGE_SUFFIX@-shell: mit-shell
	cp mit-shell $@
	chmod +x $@

mit@PACKAGE_SUFFIX@-dump.1: mit-dump.1
	cp mit-dump $@

mit@PACKAGE_SUFFIX@-shell.1: mit-shell.1
	cp mit-shell $@
endif

EXTRA_DIST = \
	$(man_MANS)		\
	mit/binding.py.in	\
	mit-dump.in	\
	mit-shell.in	\
	mit/binding.py.in

DISTCLEANFILES = $(bin_SCRIPTS) $(man_MANS)
