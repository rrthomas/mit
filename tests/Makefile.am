# Tests Makefile.am
#
# (c) Reuben Thomas 2011-2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

TEST_EXTENSIONS = .py
# Use PY_LOG_ENV to set LD_PRELOAD for ASAN
PY_LOG_COMPILER = env $(PY_LOG_ENV) $(PYTHON)

TESTS =	\
	arithmetic.py	\
	branch.py	\
	call_native.py	\
	comparison.py	\
	extra_libc.py	\
	exceptions.py	\
	hello.py	\
	init.py		\
	load_object.py	\
	logic.py	\
	memory.py	\
	numbers.py	\
	registers.py	\
	run.py		\
	save_object.py	\
	single_step.py	\
	stack.py

TESTS_ENVIRONMENT = \
	export LD_LIBRARY_PATH=$(top_builddir)/src/@objdir@; \
	export PYTHON=$(PYTHON); \
	export PYTHONPATH=$(top_srcdir)/python; \
	export srcdir=$(srcdir); \
	export builddir=$(builddir);

EXTRA_DIST = \
	$(TESTS) \
	redirect_stdout.py \
	hello.correct \
	badobj1-4 badobj2-4 badobj3-4 badobj4-4 \
	badobj1-8 badobj2-8 badobj3-8 badobj4-8 \
	testobj1-be-4 testobj1-le-4 \
	testobj1-be-8 testobj1-le-8 \
	testobj2-be-4 testobj2-le-4 \
	testobj2-be-8 testobj2-le-8
