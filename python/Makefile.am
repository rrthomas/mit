# Python bindings Makefile.am
#
# (c) Mit authors 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

PYTHON_WITH_PATH = export PYTHONPATH=$(abs_top_srcdir)/python:$(abs_top_srcdir)/src:$(abs_top_builddir)/src:$(abs_top_srcdir)/src/features; $(PYTHON)

bin_SCRIPTS = mit@PACKAGE_SUFFIX@-dump mit@PACKAGE_SUFFIX@-shell
man_MANS = mit@PACKAGE_SUFFIX@-dump.1 mit@PACKAGE_SUFFIX@-shell.1
mit_pkgpythondir = $(pkgpythondir)@PACKAGE_SUFFIX@
mit_pkgpython_PYTHON =				\
	mit/__init__.py				\
	mit/ctypes_align.py			\
	mit/int128.py				\
	mit/autonumber.py			\
	mit/globals.py				\
	mit/ipython_suppress_traceback.py	\
	mit/state.py				\
	mit/assembler.py
nodist_mit_pkgpython_PYTHON = mit/binding.py mit/errors.py mit/opcodes.py

all-local: mit/binding.py mit/errors.py mit/opcodes.py

mit/binding.py: $(top_builddir)/config.status mit/binding.py.in
	cd $(top_builddir) && $(SHELL) ./config.status $(subdir)/$@

mit/opcodes.py: gen-python-opcodes $(top_srcdir)/src/mit_core/instruction.py $(top_srcdir)/src/mit_core/vm_data.py $(top_srcdir)/src/features/extra_instructions.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-python-opcodes > mit/opcodes.py || ( rm -f mit/opcodes.py; exit 1 )

mit/errors.py: gen-python-errors $(top_srcdir)/src/mit_core/instruction.py $(top_srcdir)/src/mit_core/vm_data.py $(top_srcdir)/src/features/extra_instructions.py
	$(PYTHON_WITH_PATH) $(srcdir)/gen-python-errors > mit/errors.py || ( rm -f mit/errors.py; exit 1 )

# sloccount --autogen doesn't work (Debian bug #929000), so temporarily move
# binding.py.in during count.
loc:
	mv mit/binding.py.in mit/binding.py.in.bak && \
	$(SLOCCOUNT) --autogen $(bin_SCRIPTS) $(mit_pkgpython_PYTHON) $(nodist_mit_pkgpython_PYTHON); \
	mv mit/binding.py.in.bak mit/binding.py.in

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
	gen-python-opcodes	\
	gen-python-errors	\
	$(man_MANS)		\
	mit/binding.py.in	\
	mit-dump.in		\
	mit-shell.in

DISTCLEANFILES = $(bin_SCRIPTS) $(man_MANS) mit/errors.py mit/opcodes.py
