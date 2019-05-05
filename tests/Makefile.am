# Tests Makefile.am
#
# (c) SMite authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

TEST_EXTENSIONS = .py
# Use PY_LOG_ENV to set LD_PRELOAD for ASAN
PY_LOG_COMPILER = env $(PY_LOG_ENV) $(PYTHON)

TESTS =	\
	arithmetic.py	\
	branch.py	\
	comparison.py	\
	ext.py		\
	errors.py	\
	hello.py	\
	init.py		\
	literals.py	\
	load_object.py	\
	logic.py	\
	memory.py	\
	run.py		\
	save_object.py	\
	single_step.py	\
	stack.py

# Python will not try a relative import from a different directory, so copy
# modules from srcdir to builddir.
check_DATA = $(top_builddir)/copied-python-module-to-build

$(top_builddir)/copied-python-module-to-build:
	if ! test -e $(top_builddir)/python/@PACKAGE@/__init__.py; then \
	    $(MKDIR_P) $(top_builddir)/python/@PACKAGE@ && \
	    cp -fL $(top_srcdir)/python/@PACKAGE@/*.py $(top_builddir)/python/@PACKAGE@/ && \
	    touch $@; \
	fi

TESTS_ENVIRONMENT = \
	export LD_LIBRARY_PATH=$(top_builddir)/src/@objdir@:$$LD_LIBRARY_PATH; \
	export PYTHON=$(PYTHON); \
	export PYTHONPATH=$(top_builddir)/python; \
	export srcdir=$(srcdir);

DISTCLEANFILES = $(top_builddir)/copied-python-module-to-build

distclean-local:
	rm -rf $(top_builddir)/python/@PACKAGE@/*.py $(top_builddir)/python/@PACKAGE@/__pycache__

EXTRA_DIST = \
	$(TESTS) \
	smite_test.py	\
	redirect_stdout.py \
	hello.correct
