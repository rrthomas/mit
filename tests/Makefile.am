# Tests Makefile.am
#
# (c) Reuben Thomas 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

TEST_EXTENSIONS = .py
# Use PY_LOG_ENV to set LD_PRELOAD for ASAN
PY_LOG_COMPILER = env $(PY_LOG_ENV) $(PYTHON)

TESTS =	\
	smite_test.py	\
	arithmetic.py	\
	branch.py	\
	comparison.py	\
	extra_libc.py	\
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

TESTS_ENVIRONMENT = \
	export LD_LIBRARY_PATH=$(top_builddir)/src/@objdir@:$$LD_LIBRARY_PATH; \
	export PYTHON=$(PYTHON); \
	export PYTHONPATH=$(top_srcdir)/python; \
	export srcdir=$(srcdir); \
	export builddir=$(builddir);

EXTRA_DIST = \
	$(TESTS) \
	redirect_stdout.py \
	hello.correct \
	badobj1-le-4 badobj1-be-4 \
	badobj1-le-8 badobj1-be-8 \
	badobj2-le-4 badobj2-be-4 \
	badobj2-le-8 badobj2-be-8 \
	badobj3-le-4 badobj3-be-4 \
	badobj3-le-8 badobj3-be-8 \
	badobj4-le-4 badobj4-be-4 \
	badobj4-le-8 badobj4-be-8 \
	testobj1-be-4 testobj1-le-4 \
	testobj1-be-8 testobj1-le-8 \
	testobj2-be-4 testobj2-le-4 \
	testobj2-be-8 testobj2-le-8
