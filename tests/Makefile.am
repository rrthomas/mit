# Tests Makefile.am
#
# (c) Mit authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

TEST_EXTENSIONS = .py .bf
# Use PY_LOG_ENV to set LD_PRELOAD for ASAN
LOG_COMPILER = env $(PY_LOG_ENV)
PY_LOG_COMPILER = env $(PY_LOG_ENV) $(PYTHON)
BF_LOG_COMPILER = env $(PY_LOG_ENV) $(TIME) $(PYTHON) $(srcdir)/run-brainfuck-test

TESTS =	\
	arithmetic.py	\
	branch.py	\
	catch.py	\
	comparison.py	\
	constants.py	\
	extra.py	\
	errors.py	\
	hello.py	\
	init.py		\
	load_object.py	\
	logic.py	\
	memory.py	\
	run.py		\
	save_object.py	\
	stack.py	\
	step.py		\
	hello-world.bf  \
	cell-size.bf	\
	test-mit-shell

BENCH_TESTS = \
	mandelbrot.bf

bench:
	$(MAKE) check TESTS="$(BENCH_TESTS)"

# Python will not try a relative import from a different directory, so copy
# modules from srcdir to builddir.
check_DATA = copied-python-module-to-build

.PHONY:	copied-python-module-to-build
copied-python-module-to-build:
	if test "$(top_srcdir)" != "$(top_builddir)"; then \
	    $(MKDIR_P) $(top_builddir)/python/mit && \
	    cp -fL $(top_srcdir)/python/mit/*.py $(top_builddir)/python/mit/; \
	fi

# Augment PATH (for Windows) and LD_LIBRARY_PATH (for Linux) so that
# Python's `ctypes.find_library` find the in-tree shared libraries.
# macOS System Integrity Protection erases DYLD_LIBRARY_PATH on exec(2).
TESTS_ENVIRONMENT = \
	export PATH=$(top_builddir)/src/@objdir@:$$PATH; \
	export LD_LIBRARY_PATH=$(top_builddir)/src/@objdir@:$$LD_LIBRARY_PATH; \
	export PYTHON=$(PYTHON); \
	export PYTHONPATH=$(top_builddir)/python;

distclean-local:
	if test "$(top_builddir)" != "$(top_srcdir)"; then \
	    rm -rf $(top_builddir)/python/mit/*.py; \
	fi
	rm -rf $(top_builddir)/python/mit/__pycache__

EXTRA_DIST = \
	$(TESTS) \
	run-brainfuck-test \
	brainfuck \
	mit_test.py \
	redirect_stdout.py \
	test-mit-shell.in \
	hello.correct \
	hello-world.correct \
	cell-size.correct \
	mandelbrot.correct
