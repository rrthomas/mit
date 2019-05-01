# Python bindings Makefile.am
#
# (c) SMite authors 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

bin_SCRIPTS = @PACKAGE@-dump @PACKAGE@-shell
man_MANS = @PACKAGE@-dump.1 @PACKAGE@-shell.1
smite_pkgpythondir = $(pkgpythondir)@PACKAGE_SUFFIX@
smite_pkgpython_PYTHON =		\
	@PACKAGE@/__init__.py		\
	@PACKAGE@/__main__.py		\
	@PACKAGE@/assembler.py		\
	@PACKAGE@/vm_data.py		\
	@PACKAGE@/ext.py		\
	@PACKAGE@/instruction.py
nodist_smite_pkgpython_PYTHON = @PACKAGE@/binding.py


loc:
	$(SLOCCOUNT) $(bin_SCRIPTS) @PACKAGE@/__init__.py @PACKAGE@/__main__.py

if USING_SUFFIX
@PACKAGE@@PACKAGE_SUFFIX@-dump: @PACKAGE@-dump
	cp @PACKAGE@-dump $@
	chmod +x $@

@PACKAGE@@PACKAGE_SUFFIX@-shell: @PACKAGE@-shell
	cp @PACKAGE@-shell $@
	chmod +x $@

@PACKAGE@@PACKAGE_SUFFIX@-dump.1: @PACKAGE@-dump.1
	cp @PACKAGE@-dump $@

@PACKAGE@@PACKAGE_SUFFIX@-shell.1: @PACKAGE@-shell.1
	cp @PACKAGE@-shell $@
endif

EXTRA_DIST = \
	$(man_MANS)		\
	@PACKAGE@/binding.py.in	\
	@PACKAGE@-dump.in	\
	@PACKAGE@-shell.in

DISTCLEANFILES = $(bin_SCRIPTS) $(man_MANS)
