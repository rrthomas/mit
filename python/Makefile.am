# Python bindings Makefile.am
#
# (c) Reuben Thomas 2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

bin_SCRIPTS = @PACKAGE@-trace @PACKAGE@-dump
man_MANS = @PACKAGE@-dump.1 @PACKAGE@-trace.1
# FIXME: install as smite-shell; add man page
pkgpython_PYTHON = \
	@PACKAGE@/__init__.py \
	@PACKAGE@/__main__.py \
	@PACKAGE@/vm_data.py \
	@PACKAGE@/opcodes_extra.py

loc:
	$(CLOC) $(CLOC_OPTS) $(bin_SCRIPTS) $(pkgpython_PYTHON)

EXTRA_DIST = \
	@PACKAGE@-dump.in @PACKAGE@-dump.1
	@PACKAGE@-trace.in @PACKAGE@-trace.1

DISTCLEANFILES = @PACKAGE@-dump @PACKAGE@-dump.1 @PACKAGE@-trace @PACKAGE@-trace.1
