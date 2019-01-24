# Python bindings Makefile.am
#
# (c) Reuben Thomas 2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

bin_SCRIPTS = smite-trace @PACKAGE@-dump
# FIXME: add man page for smite-trace
man_MANS = @PACKAGE@-dump.1
# FIXME: install as smite-shell; add man page
pkgpython_PYTHON = \
	smite/__init__.py \
	smite/__main__.py \
	smite/vm_data.py \
	smite/opcodes_extra.py

loc:
	$(CLOC) $(CLOC_OPTS) $(bin_SCRIPTS) $(pkgpython_PYTHON)

EXTRA_DIST = \
	@PACKAGE@-dump.in @PACKAGE@-dump.1

DISTCLEANFILES = @PACKAGE@-dump @PACKAGE-dump.1
