# Python bindings Makefile.am
#
# (c) Reuben Thomas 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

bin_SCRIPTS = @PACKAGE@-dump @PACKAGE@-shell
man_MANS = @PACKAGE@-dump.1 @PACKAGE@-shell.1
pkgpython_PYTHON =			\
	@PACKAGE@/__init__.py		\
	@PACKAGE@/__main__.py		\
	@PACKAGE@/vm_data.py		\
	@PACKAGE@/vm_data_extra.py	\
	@PACKAGE@/instruction_gen.py

loc:
	$(SLOCCOUNT) $(bin_SCRIPTS) $(pkgpython_PYTHON)

EXTRA_DIST = \
	$(man_MANS)		\
	@PACKAGE@-dump.in	\
	@PACKAGE@-shell.in

DISTCLEANFILES = $(bin_SCRIPTS) $(man_MANS)
